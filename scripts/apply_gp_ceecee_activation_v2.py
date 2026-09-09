from pathlib import Path

tp = Path('templates/tv.html')
tv = tp.read_text(encoding='utf-8')

if 'GP_ROLE_SCOPED_CRISP_V7' in tv:
    print('Role-scoped Crisp V7 already applied')
    raise SystemExit(0)
if 'GP_CRISP_FEMALE_V6' not in tv:
    raise SystemExit('Approved Crisp V6 catalog is missing')

replacements = [
    (
"""      {name:'حريري',tracks:[
        {text:'حريري، إذا خلصت الحالة حدّثها عالشاشة دغري، مشان الكل يعرف وين صار الشغل. شغل مرتب.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/27eea06a-f160-443e-999e-d1a63bd0fa51.mp3'},
        {text:'حريري، ورجينا لمسة الخبرة اليوم. خلّص الجاهز، وخلّي الحالة تنتقل للخطوة الجاية من دون ما تضيع بين المراحل.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/ee5ae571-9eec-4db3-9609-fef5995017cb.mp3'}]},""",
"""      {name:'حريري',tracks:[
        {text:'حريري، ركّز اليوم عالأعطال الكهربائية. فحص مرتب، قياس واضح، وما نبدّل قطعة قبل ما نعرف السبب. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/8388e59d-f4ef-421f-b12b-7d3d55325312.mp3'},
        {text:'حريري، إذا العطل كهربائي خليه يمر عليك من أولها. بدنا تشخيص دقيق، توصيلات مرتبة، والحالة تتحدّث أول بأول.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/cbc9e259-062d-4860-9d4c-ef7ea488d2e0.mp3'}]},"""
    ),
    (
"""      {name:'أبو غسان',tracks:[
        {text:'أبو غسان، ركّز على الحالات اللي واقفة، وإذا في عائق ارفعه من بكير قبل ما يكبر. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/9543c73e-cee0-403c-bd9a-14657a4b2e31.mp3'},
        {text:'أبو غسان، اليوم بدنا المتابعة تمشي مع الشغل خطوة بخطوة. ما بدنا جهاز يخلص والحالة تضل واقفة عالشاشة.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/174d62a2-8392-4de1-9997-5f2d9fb763c2.mp3'}]},""",
"""      {name:'أبو غسان',tracks:[
        {text:'أبو غسان، قبل ما تطلع عالموقع تأكّد إنو الأدوات والقطع المطلوبة معك، وبعد الزيارة حدّث الحالة دغري. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/d34c52bc-4334-43bd-8011-75738ba23da5.mp3'},
        {text:'أبو غسان، شغلك بالموقع هو واجهة القصر الذهبي. خليك واضح مع الزبون، خلّص المطلوب، ورجّع كل التفاصيل عالنظام.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/8c239db0-1c08-4469-bf9c-b57fc44779c0.mp3'}]},"""
    ),
    (
"""      {name:'حازم',tracks:[
        {text:'حازم، اليوم بدنا شغل واضح من أول الفحص لآخر خطوة، وما نخلي حالة واقفة بلا سبب. تمام.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/8d57996b-0e16-413b-ba99-6db2094f1620.mp3'},
        {text:'حازم، إذا في شغلة معلّقة لا تتركها ساكتة. ارفعها من بكير وخلي الكل يعرف شو الخطوة الجاية. يعطيك العافية.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/db8fbf86-7368-47ca-a8bd-686f5676cf2e.mp3'}]}""",
"""      {name:'حازم',tracks:[
        {text:'حازم، يعطيك العافية. خلّي المكتب مرتب والضيافة جاهزة، وإذا ناقص شي خبرنا من بكير. هيك الشغل المرتب.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/d5bdfb4d-5b56-4183-9dd1-8dfe0f184c0a.mp3'},
        {text:'حازم، اليوم بدنا المكتب يضل مرتب وكل طلب يوصل بوقته. شغلك بالمكتب بيسهّل يوم الكل. تمام.',url:'https://storage.googleapis.com/adm--audio-playback--7d--public/mcp-preview/37226c6c-0637-4bb0-ae86-d81311bbc182.mp3'}]}"""
    ),
]

for old, new in replacements:
    if old not in tv:
        raise SystemExit('Expected current staff voice block was not found')
    tv = tv.replace(old, new, 1)

tv = tv.replace(
    '    // GP_CRISP_FEMALE_V6\n',
    '    // GP_CRISP_FEMALE_V6\n    // GP_ROLE_SCOPED_CRISP_V7: حريري كهرباء، أبو غسان فني مواقع، حازم دعم المكتب والضيافة.\n',
    1,
)

tp.write_text(tv, encoding='utf-8')
print('Role-scoped Crisp V7 applied')
