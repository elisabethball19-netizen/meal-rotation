"""Issue 130 helper for older tests: Start next week only works inside the due window (from 2 days before the
plan's displayed week ends). Call enter_due_window(p) before pressing it; the clock is frozen at local noon on the
window's first day, so the roll produces the same weeks the tests expected before the guard existed."""
from datetime import datetime, timezone

HOOK = '''window.sw130due={at:()=>{const s=new Date(mealPlanWeekStart(mealPlans.find(p=>p.id===activePlanId)));s.setDate(s.getDate()+7-START_WEEK_WINDOW_DAYS);s.setHours(12,0,0,0);return s.getTime()},render:()=>renderList({readOnly:true})};'''


def register(fixture):
    if 'window.sw130due' not in fixture.HOOK:
        fixture.HOOK += HOOK


def enter_due_window(p):
    ms = p.evaluate('sw130due.at()')
    p.clock.set_fixed_time(datetime.fromtimestamp(ms / 1000, tz=timezone.utc))
    p.evaluate('sw130due.render()')
