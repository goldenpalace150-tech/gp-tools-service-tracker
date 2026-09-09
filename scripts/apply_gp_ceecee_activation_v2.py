from pathlib import Path

tp = Path('templates/tv.html')
tv = tp.read_text(encoding='utf-8')

if 'GP_ACCOUNTANT_GHBEITI_V9' in tv:
    print('Accountant غبيطي V9 already applied')
    raise SystemExit(0)
if 'GP_FUNNY_BALANCED_CRISP_V8' not in tv:
    raise SystemExit('Balanced funny Crisp V8 is missing')

start = tv.find("{name:'خبيطي',tracks:[")
if start < 0:
    raise SystemExit('Active Crisp block for خبيطي was not found')
end = tv.find(']}', start)
if end < 0:
    raise SystemExit('Active Crisp block end for خبيطي was not found')
block = tv[start:end+2]
if block.count("url:'") != 3:
    raise SystemExit(f'Expected exactly three current tracks for خبيطي, found {block.count("url:")}')

replacement = """{name:'غبيطي',tracks:[
        {text:'غبيطي، يعطيك العافية. اليوم بدنا الحسابات واضحة، كل مبلغ بمكانه، وكل فاتورة مسجلة قبل ما يخلص اليوم.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/6d20d63a-a250-4239-b5a7-073ce8952f1d.mp3'},
        {text:'غبيطي، ركّز اليوم عالمطابقات والدفعات، وإذا في رقم مو راكب لا تمرّقه. خلّيه واضح قبل ما نسكّر الحساب.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/6e7f4e37-7702-465a-8e2c-f84bed3c7195.mp3'},
        {text:'غبيطي، إذا آخر اليوم طلع معك فرق بالحساب، لا تقنعنا إنو الأرقام زعلت من بعض. رجّع المطابقة وخلي كل ليرة تعرف محلها.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/953aa18a-cab4-441e-a902-c4b57dde2873.mp3'}]}"""

tv = tv[:start] + replacement + tv[end+2:]

# Keep legacy staff rotation labels aligned with the current Arabic name in case any old path is invoked.
tv = tv.replace("['أبو عدنان','خبيطي','أبو نقطة','عمر','أبو آدم','حريري','أبو غسان','حازم']", "['أبو عدنان','غبيطي','أبو نقطة','عمر','أبو آدم','حريري','أبو غسان','حازم']")
tv = tv.replace("['أبو عدنان','خبيطي','أبو نقطة','عمر','حريري','أبو غسان','حازم']", "['أبو عدنان','غبيطي','أبو نقطة','عمر','حريري','أبو غسان','حازم']")

tv = tv.replace(
    '    // GP_FUNNY_BALANCED_CRISP_V8:',
    '    // GP_ACCOUNTANT_GHBEITI_V9: غبيطي = accountant, 2 normal + 1 funny accounting clip.\n    // GP_FUNNY_BALANCED_CRISP_V8:',
    1,
)

tp.write_text(tv, encoding='utf-8')
print('Accountant غبيطي V9 applied: 2 normal + 1 funny accounting clip')
