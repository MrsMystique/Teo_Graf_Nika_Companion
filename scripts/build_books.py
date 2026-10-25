#!/usr/bin/env python3
"""Build offline illustrated reader editions; original products stay byte-identical."""
from pathlib import Path
import re, html, shutil, json
import markdown
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'books'
VERSION=(ROOT/'VERSION').read_text().strip()

def md(text): return markdown.markdown(text,extensions=['tables','fenced_code','sane_lists'])

def source_parts(product):
    path=ROOT/'originals'/('THEO_COMPANION_APPROVED_v1.md' if product=='math' else 'NIKA_COMPANION_RELEASE_CANDIDATE_v1.md')
    text=path.read_text()
    intro=text.split('## 1.')[0]
    intro=re.sub(r'^# .*\n','',intro,count=1)
    intro=re.sub(r'^\*APPROVED.*\n','',intro,flags=re.M)
    tail=text[text.index('## 2.'):]
    return intro.strip(),tail

def contents(product):
    math=product=='math'; intro,tail=source_parts(product)
    start='''## 1. Забери помощника с собой

Открой доступный ИИ-чат. Скопируй **полный промпт** из этого издания и отправь его первым сообщением в новом разговоре. Затем напиши один вопрос или пришли одно задание. Можно работать с нашей книгой, другим учебником или начать с нуля.

Если читаешь PDF, полный промпт находится в конце издания. В электронной версии кнопка копирует его целиком; TXT удобен для переноса в чат.

Если ссылка на расширенный характер недоступна, помощник продолжит по краткому описанию, уже встроенному в промпт. Покупать подписку, открывать GitHub или загружать всю книгу не требуется. Возможности чтения файлов и аудио зависят от выбранного сервиса. Помощник не должен притворяться, что прочитал недоступный материал.

Если текст не помещается, скачай PROMPT.txt и прикрепи его, если чат читает файлы. Или раздели по границе разделов и отправь частями, указав их порядок и завершение. Модель с маленьким контекстом может не удержать все инструкции; не обрезай молча правила точности и памяти.
'''
    voices=('''## Выбери, с кем разбираться

**Тео** — спокойный, точный, наблюдательный. Поможет прочитать условие, увидеть ограничения и понять, почему способ работает. Его ирония относится к математической ситуации, а не к тебе.

**Граф** — любопытный, находчивый и немного честолюбивый. Он любит проверять смелые идеи и искать короткий путь. Его живость не означает менее точную математику: он умеет объяснять самостоятельно.

Напиши **«Позови Графа»**, чтобы сменить ведущего, или **«Верни Тео»**, чтобы вернуться. Уже сделанные шаги, режим подсказок и прогресс сохраняются. По умолчанию говорит один герой; спектакль из перебранок не обязателен. Два персонажа одной модели не считаются двумя независимыми экспертами.

Можно попросить **«Без юмора»** или **«Нейтральный голос»**. На полноту объяснения это не влияет.
''' if math else '''## Ника — узнаваемая, а объяснение — настоящее

Живая, наблюдательная, музыкальная, с чувством юмора и собственным характером. Ника объясняет, что человек хочет сказать, почему выбирает эту форму и как её услышит собеседник. Она не обязана шутить в каждом ответе и не будет превращать тебя в объект шутки.

Новые английские примеры сопровождаются естественным русским переводом, пока он нужен. Можно попросить **«Английский без перевода»**, **«Без юмора»** или **«Нейтральный голос»**.

Ника различает ошибку, другой допустимый смысл, разговорный вариант и стилистическое предпочтение. Один правильный ответ — хорошее наблюдение, но не автоматическое свидетельство, что вся тема уже освоена.
''')
    # Keep all original reader-facing sections 2–6; the v2 prompt supplies updated memory fields.
    tail=tail.replace('Помощник должен ответить по-русски', 'Помощник должен ответить по-русски')
    close='''## Что останется после занятия

Не только ответ, но и понятный способ: что ты заметил, почему выбрал этот шаг и чем проверил результат. Помощь постепенно уменьшается — от полного разбора к небольшому ключу и самостоятельной попытке.

Можно попросить **«Сначала покажи решение целиком»**. Можно — **«Без подсказок, сначала попробую сам»**. Хорошее занятие подстраивается под задачу, а не удерживает тебя в бесконечных вопросах.

Перед уходом сохрани одну полную заметку о прогрессе. Она различает самостоятельную работу, помощь и то, что пока только объяснили. В следующий чат ты принесёшь эту заметку — не обещание магической памяти.
'''
    return intro,start,voices,tail,close

def render(product):
    math=product=='math'
    title='Тео и Граф' if math else 'Ника'
    subtitle='Математический компаньон' if math else 'English Companion'
    tagline='Даже в хаосе есть логика.' if math else 'У языка есть своя музыка.'
    intro,start,voices,tail,close=contents(product)
    prompt=(ROOT/f'products/{product}/PROMPT.txt').read_text()
    (OUT/'prompts').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/f'products/{product}/PROMPT.txt',OUT/f'prompts/{product}-PROMPT.txt')
    sections=[]
    # Intro is preserved from original, split only by presentation.
    sections.append(('hello','На первой странице',intro))
    sections.append(('start','Начать',start))
    sections.append(('voice','Твой голос',voices))
    for i,part in enumerate(re.split(r'(?m)(?=^## [2-6]\.)',tail)):
        if not part.strip():continue
        heading=part.splitlines()[0].removeprefix('## ')
        sections.append((f'guide-{i}',heading,part))
    sections.append(('finish','Продолжить завтра',close))
    links=''.join('<a href="#%s"><span>%02d</span>%s</a>' % (key, i, html.escape(re.sub(r"^\d+\.\s*", "", label))) for i,(key,label,_) in enumerate(sections,1))
    body=[]
    for key,label,text in sections:
        extra=''
        if key=='start':
            extra=f'''<div class="takeaway"><span class="tiny">ТВОЙ ПОМОЩНИК · ПОЛНЫЙ ТЕКСТ</span><h3>Скопируй. Открой чат.<br>Начни с одного вопроса.</h3><div class="actions"><button class="button ink" data-copy-prompt>Скопировать промпт <span aria-hidden="true">↗</span></button><a class="text-link" href="prompts/{product}-PROMPT.txt" download>Скачать TXT ↓</a></div><p class="copy-status" role="status" aria-live="polite"></p></div>'''
        if key=='voice' and math:
            extra='''<div class="voice-demo"><span class="tiny">ОДНА ЗАДАЧА · ДВА ГОЛОСА</span><h3>Почему НОК(n; 25) = 25?</h3><div class="voice-tabs" role="group" aria-label="Пример голоса"><button aria-pressed="true" data-voice="theo">Тео</button><button aria-pressed="false" data-voice="graf">Граф</button></div><h4 class="print-voice-label">Тео</h4><div class="voice-quote" aria-live="polite">Здесь известен результат НОК, а n нужно найти. Число n должно делить 25. Все натуральные решения: 1, 5, 25. Для каждого НОК с 25 равен 25; других решений нет, поскольку других натуральных делителей у 25 нет.</div><div class="print-graf"><h4>Граф</h4><p>Хочется записать n = 25 и объявить дело закрытым. Но слово «все» переживает такие торжественные заявления. Если 25 — общее кратное, оно делится на n. Значит, берём все натуральные делители 25: 1, 5, 25. Каждый подходит; других делителей нет.</p></div><p class="small">Новый пример интонации, не цитата из книги. Переключатель показывает пример; само занятие проходит в выбранном тобой ИИ-чате.</p></div>'''
        if key=='voice' and not math:
            extra='''<div class="voice-demo"><span class="tiny">ОТ СМЫСЛА К ФОРМЕ</span><h3>Does she have a guitar?</h3><p class="translation">У неё есть гитара?</p><p>В обычном вопросе Present Simple с лексическим глаголом показатель третьего лица уже находится в <strong>does</strong>. Поэтому основной глагол — <strong>have</strong>, а не has.</p><p>Но <strong>Is she tired?</strong> — «Она устала?» — строится с be. Одно правило не должно притворяться всем английским сразу.</p><p class="small">Новый демонстрационный пример, не цитата из книги.</p></div>'''
        body.append(f'<section class="reader-section" id="{key}">{md(text)}{extra}</section>')
    name='math' if math else 'english';other='english' if math else 'math'
    art='theo' if math else 'nika'
    bookmd=f'# {title} · {subtitle}\n\n*{tagline}*\n\n'+ '\n\n'.join(x[2] for x in sections)+ '\n\n## Полный промпт\n\n```text\n'+prompt+'\n```\n'
    (OUT/f'{name}-BOOK.md').write_text(bookmd)
    template=f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · {subtitle}</title><meta name="description" content="Подарочный учебный компаньон: понятный запуск, готовый промпт и переносимый прогресс."><link rel="stylesheet" href="assets/book.css"></head>
<body class="{name}"><a class="skip" href="#hello">К тексту</a><header class="top"><a class="brand" href="START.html">На одном листе<span>Подарочная коллекция</span></a><nav aria-label="Издания"><a href="english.html" {'aria-current="page"' if not math else ''}>Ника</a><a href="math.html" {'aria-current="page"' if math else ''}>Тео и Граф</a><button class="print-button" onclick="window.print()">Печать / PDF ↗</button></nav></header>
<main><section class="cover" aria-labelledby="book-title"><div class="cover-copy"><span class="eyebrow">{subtitle}</span><h1 id="book-title">{title}</h1><p class="tagline">{tagline}</p><div class="pencil-line"></div><p class="lead">{'Понимать устройство задачи.<br>Находить свой способ.<br>Проверять, а не угадывать.' if math else 'Понимать смысл.<br>Замечать закономерность.<br>Говорить своим голосом.'}</p><a class="button" href="#start">Забрать помощника <span aria-hidden="true">↗</span></a><p class="hand-note">Один вопрос — уже хорошее начало.</p></div><figure><img class="cover-art" src="assets/{art}-cover.png" width="{1024 if math else 1055}" height="{1536 if math else 1491}" alt="{'Тео и Граф в библиотеке на обложке математического компаньона' if math else 'Ника на обложке английского компаньона'}"><figcaption>{'Тео · Граф · Империя Чисел' if math else 'Ника · музыка, язык и живые истории'}</figcaption></figure></section>
<div class="book-body"><aside id="contents" class="outline" aria-label="На этом листе"><p class="tiny">НА ЭТОМ ЛИСТЕ</p>{links}<a href="#full-prompt"><span aria-hidden="true"><svg width="12" height="12" viewBox="0 0 14 14"><path d="M2 12L12 2M3 2h9v9" fill="none" stroke="currentColor"/></svg></span>Полный промпт</a><a class="other-book" href="{other}.html">{'Английский с Никой' if math else 'Математика с Тео и Графом'} ↗</a></aside><article>{''.join(body)}
<section id="full-prompt" class="reader-section appendix"><span class="tiny">МОЖНО ВЗЯТЬ С СОБОЙ</span><h2>Полный промпт</h2><p>Весь текст ниже — одна инструкция для нового ИИ-чата. Короткий характер уже внутри; расширенные профили подключаются, только если чат действительно умеет их читать.</p><div class="actions"><button class="button ink" data-copy-prompt>Скопировать весь промпт ↗</button><a class="text-link" href="prompts/{product}-PROMPT.txt" download>Скачать TXT ↓</a></div><p class="copy-status" role="status" aria-live="polite"></p><details class="prompt-details"><summary>Показать полный текст инструкции</summary><pre id="prompt-text">{html.escape(prompt)}</pre></details><noscript><p>JavaScript выключен: открой полный текст выше или скачай TXT и скопируй вручную.</p></noscript></section>
</article></div>
<section class="last-leaf"><figure><img src="assets/{art}-finish.png" width="{1024 if math else 1086}" height="{1536 if math else 1448}" alt="{'Тео и Граф за работой в библиотеке' if math else 'Ника протягивает руку читателю на заключительной иллюстрации'}"></figure><div><span class="eyebrow">ДАЛЬШЕ — ТВОЯ ИСТОРИЯ</span><h2>{'Красивое решение<br>начинается с понимания.' if math else 'Сначала одна фраза.<br>Потом — свой голос.'}</h2><p>Тебе не нужно знать всё до начала.<br>Достаточно принести то, что пока не складывается.</p><a class="text-link" href="#start">Вернуться к промпту ↑</a></div></section>
</main><nav class="mobile-dock" aria-label="Навигация по изданию"><a href="#contents">Содержание ↑</a><a href="#start">Забрать промпт ↗</a></nav><footer><span class="brand">На одном листе.</span><p>Версия {VERSION} · читательский макет для авторского просмотра.<br>ИИ может ошибаться. Проверяй важное; сохраняй прогресс у себя.</p><a href="START.html">Вся коллекция ↗</a></footer><script src="assets/book.js"></script></body></html>'''
    (OUT/f'{name}.html').write_text(template)

def main():
    OUT.mkdir(exist_ok=True)
    for subject in ['math','english']:render(subject)
    (OUT/'START.html').write_text('''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>На одном листе · Подарочная коллекция</title><link rel="stylesheet" href="assets/book.css"></head><body><main class="collection"><span class="eyebrow">НА ОДНОМ ЛИСТЕ · ПОДАРОЧНАЯ КОЛЛЕКЦИЯ</span><h1>Кого позовём?</h1><p>Два предмета. Три характера.<br>Одна цель — понять и научиться самому.</p><div class="collection-grid"><a href="english.html"><img src="assets/nika-cover.png" alt="Обложка английского компаньона Ники"><h2>Ника</h2><p>Английский: смысл, форма и живой разговор.</p><span>Открыть издание ↗</span></a><a href="math.html"><img src="assets/theo-cover.png" alt="Обложка математического компаньона Тео и Графа"><h2>Тео и Граф</h2><p>Математика: устройство, метод и проверка.</p><span>Открыть издание ↗</span></a></div><p class="small">Эти издания открываются без интернета. Для самого занятия нужен доступный ИИ-чат.<br>Внутри — полный промпт, примеры запуска и инструкция сохранения прогресса.</p></main></body></html>''')
    print('Built two full illustrated books and collection entry.')
if __name__=='__main__':main()
