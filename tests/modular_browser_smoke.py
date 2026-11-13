"""Dependency-free Chromium smoke check for the plain-script application."""
import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from urllib.parse import urlparse


def read_exact(sock, length):
    result = b""
    while len(result) < length:
        chunk = sock.recv(length - len(result))
        if not chunk:
            raise EOFError("Chromium closed the debugging connection")
        result += chunk
    return result


def receive(sock):
    first, second = read_exact(sock, 2)
    size = second & 127
    if size == 126:
        size = struct.unpack("!H", read_exact(sock, 2))[0]
    elif size == 127:
        size = struct.unpack("!Q", read_exact(sock, 8))[0]
    payload = read_exact(sock, size)
    if first & 15 != 1:
        return {}
    return json.loads(payload)


def send(sock, message):
    data = json.dumps(message).encode()
    mask = os.urandom(4)
    size = len(data)
    header = bytes([129, 128 | (size if size < 126 else 126)])
    if size >= 126:
        header += struct.pack("!H", size)
    sock.sendall(header + mask + bytes(v ^ mask[i % 4] for i, v in enumerate(data)))


def run(url, flows=False, checks=None):
    with tempfile.TemporaryDirectory(prefix="meal-smoke-", ignore_cleanup_errors=True) as profile:
        process = subprocess.Popen([
            shutil.which("chromium") or "chromium", "--headless", "--no-sandbox",
            "--disable-gpu", "--disable-dev-shm-usage",
            "--remote-debugging-port=0", "--remote-allow-origins=*",
            "--user-data-dir=" + profile, "about:blank"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sock = None
        try:
            active_port = os.path.join(profile, "DevToolsActivePort")
            deadline = time.time() + 15
            while not os.path.exists(active_port):
                if time.time() > deadline:
                    raise TimeoutError("Chromium did not start")
                time.sleep(0.1)
            with open(active_port) as source:
                port = int(source.readline())
            targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list"))
            target = next(t for t in targets if t["type"] == "page")
            endpoint = urlparse(target["webSocketDebuggerUrl"])
            sock = socket.create_connection((endpoint.hostname, endpoint.port))
            key = base64.b64encode(os.urandom(16)).decode()
            sock.sendall((
                f"GET {endpoint.path} HTTP/1.1\r\nHost: {endpoint.netloc}\r\n"
                "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode())
            response = b""
            while b"\r\n\r\n" not in response:
                response += sock.recv(4096)
            assert b"101" in response.split(b"\r\n")[0], response
            sock.settimeout(0.5)
            send(sock, {"id": 1, "method": "Runtime.enable"})
            send(sock, {"id": 2, "method": "Page.navigate", "params": {"url": url}})
            errors = []
            deadline = time.time() + 7
            while time.time() < deadline:
                try:
                    message = receive(sock)
                except socket.timeout:
                    continue
                if message.get("method") == "Runtime.exceptionThrown":
                    errors.append(message["params"]["exceptionDetails"].get("exception", {}).get("description", str(message)))
                if message.get("method") == "Runtime.consoleAPICalled" and message["params"]["type"] == "error":
                    errors.append(str(message["params"]["args"]))
            send(sock, {"id": 3, "method": "Runtime.evaluate", "params": {
                "expression": "({title:document.title,recovery:document.getElementById('mealRecoveryStatus')?.textContent||null,tabs:document.getElementById('tabs')?.children.length||0})",
                "returnByValue": True
            }})
            deadline = time.time() + 5
            while time.time() < deadline:
                message = receive(sock)
                if message.get("id") == 3:
                    result = message["result"]["result"].get("value", {})
                    break
            else:
                raise TimeoutError("No rendered-page result")
            print(json.dumps({"page": result, "consoleErrors": errors}, indent=2))
            assert not errors, "Browser JavaScript errors were reported"
            assert result.get("recovery") is None, "App unexpectedly entered recovery"
            assert result.get("tabs", 0) > 0, "App did not render its navigation"
            if flows or checks:
                sequence = 10

                def command(method, params=None):
                    nonlocal sequence
                    sequence += 1
                    request_id = sequence
                    send(sock, {"id": request_id, "method": method, "params": params or {}})
                    until = time.time() + 10
                    while time.time() < until:
                        try:
                            message = receive(sock)
                        except socket.timeout:
                            continue
                        if message.get("method") == "Runtime.exceptionThrown":
                            errors.append(message["params"]["exceptionDetails"].get("exception", {}).get("description", str(message)))
                        if message.get("method") == "Runtime.consoleAPICalled" and message["params"]["type"] == "error":
                            errors.append(str(message["params"]["args"]))
                        if message.get("id") == request_id:
                            if "error" in message:
                                raise ValueError(str(message["error"]))
                            return message["result"]
                    raise TimeoutError(method)

                def evaluate(expression):
                    response = command("Runtime.evaluate", {
                        "expression": expression, "returnByValue": True, "awaitPromise": True
                    })
                    if "exceptionDetails" in response:
                        raise ValueError(str(response["exceptionDetails"]))
                    return response["result"].get("value")

                def wait_for(expression):
                    until = time.time() + 15
                    while time.time() < until:
                        try:
                            if evaluate(expression):
                                return
                        except ValueError:
                            pass  # Reloads briefly destroy the old execution context.
                        time.sleep(0.1)
                    raise AssertionError("Timed out: " + expression)

                if checks:
                    checks(evaluate, command, wait_for, errors)
                    if not flows:
                        return

                evaluate("""(()=>{window.localStorage.setItem('mealRotationDataV1','{broken');
                    window.localStorage.setItem('mealRotationRecoveryJournalV1','{broken');
                    window.localStorage.setItem('qa-unrelated','keep')})()""")
                command("Page.reload")
                wait_for("!!document.getElementById('mealRecoveryStatus')")
                evaluate("""(()=>{
                    const native=Storage.prototype.setItem;
                    native.call(sessionStorage,'qa-quota-write-attempts','0');
                    Storage.prototype.setItem=function(k,v){
                        if(this===window.localStorage){
                            native.call(sessionStorage,'qa-quota-write-attempts',String(Number(sessionStorage.getItem('qa-quota-write-attempts'))+1));
                            throw new DOMException('Test quota full','QuotaExceededError');
                        }
                        return native.call(this,k,v);
                    };
                    [...document.querySelectorAll('button')].find(b=>b.textContent==='Start Fresh').click();
                    [...document.querySelectorAll('button')].find(b=>b.textContent==='Confirm Start Fresh').click();
                })()""")
                wait_for("document.readyState==='complete'&&!document.getElementById('mealDataRecovery')&&document.getElementById('tabs')?.children.length>0")
                fresh = evaluate("""({
                    attempts:sessionStorage.getItem('qa-quota-write-attempts'),
                    journal:window.localStorage.getItem('mealRotationRecoveryJournalV1'),
                    unrelated:window.localStorage.getItem('qa-unrelated'),
                    core:window.localStorage.getItem('mealRotationDataV1')
                })""")
                assert fresh["attempts"] == "0", fresh
                assert fresh["journal"] is None, fresh
                assert fresh["unrelated"] == "keep", fresh
                assert not fresh["core"] or json.loads(fresh["core"])["meals"] == [], fresh
                print("PASS: clicked Confirm Start Fresh under forced quota failure; zero writes, journal cleared, normal app reloaded.")

                backup = {
                    "version": 2, "cats": ["QA Dinner"], "active": "QA Dinner",
                    "meals": [
                        {"id": 101, "name": "QA Soup", "cat": "QA Dinner", "ingredients": ["salt"], "instructions": ["Simmer."], "rotation": True},
                        {"id": 102, "name": "QA Pasta", "cat": "QA Dinner", "ingredients": ["pasta"], "instructions": ["Boil."], "rotation": True}
                    ],
                    "weekdayCategories": {"Monday": ["QA Dinner"]},
                    "weekdayMealOverrides": {"Monday::QA Dinner": "102"},
                    "mealPlans": {"activeId": "qa-week", "plans": [{
                        "id": "qa-week", "name": "QA Week",
                        "weekdayCategories": {"Monday": ["QA Dinner"]},
                        "weekdayMealOverrides": {"Monday::QA Dinner": "102"},
                        "weekdayRecipeFilters": {}, "pinnedCats": ["QA Dinner"],
                        "autoPinTopCategories": True, "weekSchedule": {"version": 1, "slots": {}, "order": {}}
                    }]},
                    "cookSessions": {"version": 1, "occurrences": {
                        '["qa-week","Monday","102",""]': {
                            "id": "qa-progress",
                            "context": {"planId": "qa-week", "day": "Monday", "cat": "QA Dinner", "mealId": "102", "parentId": ""},
                            "ingredients": [], "steps": []
                        }
                    }},
                    "checkedIngredients": ["pasta"],
                    "storage": {"mealRotationExtensionV1": "keep-extension", "mealRotationCompactFractionsMigratedV2": "true"}
                }
                evaluate("window.localStorage.setItem('mealRotationDataV1'," + json.dumps(json.dumps({
                    "cats": ["Before"], "active": "Before", "meals": []
                })) + ")")
                command("Page.reload")
                wait_for("document.readyState==='complete'&&!document.getElementById('mealDataRecovery')&&document.getElementById('tabs')?.children.length>0")
                evaluate("""(()=>{
                    const text=BACKUP,original=HTMLInputElement.prototype.click;
                    window.confirm=()=>true;
                    HTMLInputElement.prototype.click=function(){
                        if(this.type!=='file')return original.call(this);
                        sessionStorage.setItem('qa-file-accept',this.accept);
                        Object.defineProperty(this,'files',{value:[new File([text],'qa-backup.json',{type:'application/json'})]});
                        this.dispatchEvent(new Event('change'));
                    };
                    document.getElementById('settings').click();
                    [...document.querySelectorAll('button')].find(b=>b.textContent==='Restore backup').click();
                })()""".replace("BACKUP", json.dumps(json.dumps(backup))))
                wait_for("document.readyState==='complete'&&typeof meals!=='undefined'&&meals.some(m=>m.id===102)&&activePlanId==='qa-week'&&!document.getElementById('mealDataRecovery')")
                restored = evaluate("""({
                    core:JSON.parse(window.localStorage.getItem('mealRotationDataV1')),
                    plans:JSON.parse(window.localStorage.getItem('mealRotationPlansV1')),
                    assignments:JSON.parse(window.localStorage.getItem('mealRotationWeekdayCategoriesV1')),
                    overrides:JSON.parse(window.localStorage.getItem('mealRotationWeekdayMealOverridesV1')),
                    sessions:JSON.parse(window.localStorage.getItem('mealRotationCookingSessionsV1')),
                    checked:JSON.parse(window.localStorage.getItem('mealRotationCheckedIngredientsV1')),
                    extension:window.localStorage.getItem('mealRotationExtensionV1'),
                    accept:sessionStorage.getItem('qa-file-accept')
                })""")
                assert restored["core"]["cats"] == backup["cats"], restored
                for expected in backup["meals"]:
                    actual = next(m for m in restored["core"]["meals"] if m["id"] == expected["id"])
                    for field in ("id", "name", "cat", "ingredients"):
                        assert actual[field] == expected[field], (field, actual)
                assert restored["plans"]["activeId"] == "qa-week", restored
                assert restored["plans"]["plans"][0]["name"] == "QA Week", restored
                assert restored["assignments"] == backup["weekdayCategories"], restored
                assert restored["overrides"] == backup["weekdayMealOverrides"], restored
                assert restored["sessions"] == backup["cookSessions"], restored
                assert restored["checked"] == backup["checkedIngredients"], restored
                assert restored["extension"] == "keep-extension", restored
                assert restored["accept"] == ".json,application/json,*/*", restored
                assert not errors, errors
                print("PASS: imported a version-2 JSON file through the file-input handler; both recipes, categories, plan/weekday overrides, cooking sessions, checked ingredients and extension storage survived reload.")
                print("PASS: zero browser JavaScript errors across both journeys.")
        finally:
            if sock:
                sock.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://" + os.environ.get("REPLIT_DEV_DOMAIN", "localhost"))
    parser.add_argument("--flows", action="store_true", help="Exercise quota recovery and full JSON restore in an isolated browser")
    args = parser.parse_args()
    run(args.url, args.flows)
