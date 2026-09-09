from pathlib import Path

tp = Path('templates/tv.html')
tv = tp.read_text(encoding='utf-8')

if 'GP_FUNNY_BALANCED_CRISP_V8' in tv:
    print('Balanced funny Crisp V8 already applied')
    raise SystemExit(0)
if 'GP_ROLE_SCOPED_CRISP_V7' not in tv:
    raise SystemExit('Role-scoped Crisp V7 is missing')

jokes = {
    'أبو عدنان': ("أبو عدنان، إذا الجهاز قرر يعمل حاله أذكى منّا اليوم، ذكّره بهدوء إنو آخر شي رح ينحط عالطاولة ويتفحص قطعة قطعة. يعطيك العافية.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/03a682f7-3068-4682-ade4-1084a53de1ae.mp3'),
    'خبيطي': ("خبيطي، إذا جهاز حاول يقنعك إنو العطل لحاله رح يروح، لا تناقشه كتير. افتح العدة وخليه يعرف إنو اليوم ما في عطلة. شدّ الهمة.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/bf344609-8515-402e-8fd2-1d60ca6842cd.mp3'),
    'أبو نقطة': ("أبو نقطة، اليوم إذا الحالة صار إلها نقاط أكتر من دفتر الحسابات، وقف وعدّها من جديد. آخر نقطة بدنا ياها دايماً: تم الإنجاز.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/a298024e-8371-4d5e-9414-771fc74a0950.mp3'),
    'عمر': ("عمر، إذا قائمة الانتظار عم تكبر أسرع من القهوة عم تخلص، معناتها بدنا نسرّع شوي. خلّينا ننقصها حالة ورا حالة قبل ما تطلب مكتب لحالها.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/8627e48c-aa36-4697-93ab-71e07fc1a193.mp3'),
    'أبو آدم': ("أبو آدم، إذا كل تطوير صغير فتحلنا ثلاث أفكار تطوير جديدة، معناتها العمليات عندك ما عاد إلها نهاية. بس طالما الداشبورد عم يخضر، منسامحك هالمرة.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/38018934-84a6-4d6a-b21f-6e3b67fb1612.mp3'),
    'حريري': ("حريري، إذا الكهربا قررت تلعب غميضة اليوم، خليك أهدى منها. قيسها صح قبل ما تبدّل نص الجهاز وتكتشف إنو المشكلة من فيشة.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/a46b1f11-2645-4d4f-9e52-5ff31520e146.mp3'),
    'أبو غسان': ("أبو غسان، قبل ما تطلع عالموقع تأكّد إنو كل شي معك، لأنو أسوأ شي توصل لعند الزبون وتكتشف إنو القطعة المهمة بعدها عم تتفرج علينا من المستودع.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/31844648-2506-454d-9014-ec434fc4c6b8.mp3'),
    'حازم': ("حازم، إذا القهوة خلصت قبل الشغل اليوم، اعتبرها حالة طوارئ مكتبية. بس لا تخلي الضيافة أسرع من الطلبات، بدنا الاتنين يوصلوا بوقتهم.", 'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/4f1ef095-2973-41ca-b937-0a43c4d8d2eb.mp3'),
}

for name, (text, url) in jokes.items():
    start = tv.find("{name:'" + name + "',tracks:[")
    if start < 0:
        raise SystemExit(f'Staff block missing: {name}')
    end = tv.find(']}', start)
    if end < 0:
        raise SystemExit(f'Staff block end missing: {name}')
    block = tv[start:end+2]
    if block.count("url:'") != 2:
        raise SystemExit(f'Expected exactly two current tracks for {name}, found {block.count("url:")})')
    joke = ",\n        {text:'" + text.replace("'", "\\'") + "',url:'" + url + "'}"
    new_block = block[:-2] + joke + block[-2:]
    tv = tv[:start] + new_block + tv[end+2:]

tv = tv.replace(
    '    // GP_ROLE_SCOPED_CRISP_V7:',
    '    // GP_FUNNY_BALANCED_CRISP_V8: exactly 2 normal + 1 funny clip per staff member.\n    // GP_ROLE_SCOPED_CRISP_V7:',
    1,
)

tp.write_text(tv, encoding='utf-8')
print('Balanced funny Crisp V8 applied: 8 staff x 3 tracks')
