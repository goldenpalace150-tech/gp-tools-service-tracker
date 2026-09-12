from pathlib import Path

path = Path('tools_tracker.py')
text = path.read_text(encoding='utf-8')

start_marker = '    # GP_TV_CONTROL_AND_PUSH_UI_V1\n'
end_marker = '    # GP_MANUAL_TV_ANNOUNCEMENT_UI_V1\n'

start = text.find(start_marker)
end = text.find(end_marker, start + len(start_marker))
if start < 0 or end < 0:
    raise SystemExit('TV control markers not found')

replacement = '''    # GP_TV_CONTROL_AND_PUSH_UI_V8\n    # AppDeploy rejects direct server-to-server calls from the Streamlit host with 403.\n    # Keep the control UI inside AppDeploy so @appdeploy/client can use the supported\n    # same-origin transport, then embed that compact page here.\n    with st.expander("📺 تحكم شاشة الورشة (TV Control)", expanded=False):\n        st.components.v1.iframe(\n            "https://gp.18-232-7-146.sslip.io/control.html",\n            height=410,\n            scrolling=False,\n        )\n        st.caption("التحكم يعمل مباشرة عبر AppDeploy لتفادي خطأ 403، ويعرض تأكيد التلفزيون داخل نفس اللوحة.")\n\n'''

new_text = text[:start] + replacement + text[end:]
if new_text == text:
    raise SystemExit('No changes produced')
path.write_text(new_text, encoding='utf-8')
print('Embedded same-origin AppDeploy TV control page into tools_tracker.py')
