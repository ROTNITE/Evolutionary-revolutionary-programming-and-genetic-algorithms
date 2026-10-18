"""Сборка PDF отчета из фактических outputs/results."""
from pathlib import Path
import json, csv, html, textwrap, hashlib
from reportlab.platypus import (BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,
                                Image,Table,TableStyle,KeepTogether,Preformatted,NextPageTemplate,
                                CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER,TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

BASE=Path(__file__).resolve().parent
OUT=BASE/'Лабораторная работа № 2 — дискретная оптимизация — демонстрационный V3.pdf'
DATA=BASE/'results'
s=json.loads((DATA/'summary.json').read_text(encoding='utf-8'))
rows=list(csv.DictReader((DATA/'runs.csv').open(encoding='utf-8')))
items=list(csv.DictReader((DATA/'items.csv').open(encoding='utf-8')))
BLUE=HexColor('#163555')
MID=HexColor('#315c82')
PALE=HexColor('#edf3f8')
GRAY=HexColor('#536170')

pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DV-B','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DVM','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-B',italic='DV',boldItalic='DV-B')

BODY=ParagraphStyle('Body',fontName='DV',fontSize=9.2,leading=14.1,spaceAfter=7,textColor=HexColor('#1f2937'))
SMALL=ParagraphStyle('Small',parent=BODY,fontSize=8,leading=11.8,spaceAfter=5)
CAP=ParagraphStyle('Caption',parent=SMALL,fontSize=8.5,textColor=GRAY,alignment=TA_CENTER,spaceBefore=5,spaceAfter=12)
H1=ParagraphStyle('H1',fontName='DV-B',fontSize=15.5,leading=20,spaceBefore=17,spaceAfter=11,textColor=BLUE,keepWithNext=True)
H2=ParagraphStyle('H2',fontName='DV-B',fontSize=11.3,leading=15,spaceBefore=12,spaceAfter=7,textColor=MID,keepWithNext=True)
TITLE=ParagraphStyle('Title',fontName='DV-B',fontSize=21,leading=29,textColor=BLUE,alignment=TA_CENTER)
SUBTITLE=ParagraphStyle('Subtitle',fontName='DV',fontSize=12,leading=17,alignment=TA_CENTER,textColor=MID)
TH=ParagraphStyle('TH',fontName='DV-B',fontSize=7.2,leading=9.6,textColor=colors.white)
TC=ParagraphStyle('TC',fontName='DV',fontSize=7.2,leading=9.8)
CODE=ParagraphStyle('CODE',fontName='DVM',fontSize=7.0,leading=10)
QSTYLE=ParagraphStyle('QSTYLE',fontName='DV-B',fontSize=9.0,leading=12.7,spaceBefore=7,spaceAfter=3,textColor=MID,keepWithNext=True)


def safe(x):return html.escape(str(x))
def para(text,style=BODY):return Paragraph(text,style)
def raw(text,style=BODY):return Paragraph(safe(text),style)
def formula(text):
    return para('<font name="DVM" size="9">'+safe(text)+'</font>')

def table(headers,data,widths=None,fs=7.4,repeatRows=1):
    heading=[para(safe(h),TH) for h in headers]
    cooked=[[para(safe(v),TC) for v in row] for row in data]
    tab=Table([heading]+cooked,colWidths=widths,repeatRows=repeatRows,hAlign='LEFT')
    tab.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),BLUE),('GRID',(0,0),(-1,-1),0.25,HexColor('#cbd5e1')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),
        ('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,1),(-1,-1),
         [colors.white,HexColor('#f4f7fa')]),
    ]))
    return tab

class Report(BaseDocTemplate):
    def __init__(self,filename,**kw):
        BaseDocTemplate.__init__(self,filename,pagesize=A4,leftMargin=47,rightMargin=45,
                                 topMargin=52,bottomMargin=49,**kw)
        self.frame=Frame(self.leftMargin,self.bottomMargin,self.width,self.height,
                         leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,showBoundary=0)
        self.addPageTemplates([PageTemplate(id='normal',frames=self.frame,onPage=self.draw_page)])
        self.heading_count=0
    def draw_page(self,canvas,doc):
        canvas.saveState()
        w,h=A4
        canvas.setStrokeColor(HexColor('#c7d4e1'));canvas.setLineWidth(.6)
        canvas.line(47,h-36,w-45,h-36)
        canvas.setFont('DV',7.7);canvas.setFillColor(GRAY)
        canvas.drawString(47,h-27,'НИЯУ МИФИ · Эволюционное программирование и генетические алгоритмы')
        canvas.line(47,40,w-45,40)
        canvas.drawRightString(w-45,27,f'{doc.page}')
        canvas.drawString(47,27,'Лабораторная работа № 2 · Демонстрационный вариант V=3')
        canvas.restoreState()
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name in ('H1','H2'):
            level=0 if flowable.style.name=='H1' else 1
            title=flowable.getPlainText()
            key='section-'+hashlib.md5(title.encode('utf-8')).hexdigest()[:12]
            self.canv.bookmarkPage(key)
            if level==0:self.canv.addOutlineEntry(title,key,level=0,closed=False)
            if title != 'Оглавление':
                self.notify('TOCEntry',(level,title,self.page,key))

story=[]
def A(elem):story.append(elem)
def P(s):A(para(s))
def RAW(s):A(raw(s))
def H(s):A(para(s,H1))
def SH(s):A(para(s,H2))
def FIG(filename,caption,width=490):
    path=DATA/filename
    from PIL import Image as PILImage
    with PILImage.open(path) as i:w,h=i.size
    A(Image(str(path),width=width,height=width*h/w))
    A(para(caption,CAP))

# Title page
A(Spacer(1,93));A(para('НИЯУ МИФИ',TITLE))
A(Spacer(1,28));A(para('Дисциплина: «Эволюционное программирование<br/>и генетические алгоритмы»',SUBTITLE))
A(Spacer(1,45));A(para('ЛАБОРАТОРНАЯ РАБОТА № 2',TITLE))
A(Spacer(1,20));A(para('Генетический алгоритм для дискретной задачи<br/>с ограничениями',SUBTITLE))
A(Spacer(1,30));A(para('<b>Демонстрационный вариант V=3:</b><br/>рюкзак с обязательными и взаимоисключающими предметами',SUBTITLE))
A(Spacer(1,40));A(para('Проверяемая реализация на Python · 80 независимых запусков · фактические результаты',SUBTITLE))
A(Spacer(1,80));A(para('2026',SUBTITLE));A(PageBreak())

H('Оглавление')
toc=TableOfContents()
toc.levelStyles=[ParagraphStyle('t0',fontName='DV',fontSize=9.2,leading=15.5,leftIndent=2,firstLineIndent=0,spaceBefore=1),
                 ParagraphStyle('t1',fontName='DV',fontSize=8,leading=10.8,leftIndent=18,spaceBefore=0)]
A(toc)
A(Spacer(1,20))
P('В отчёте использованы только предоставленная методичка (стр. 2–3, 8–12) и фотографии рукописного конспекта (разделы о бинарных хромосомах, селекции, кроссовере, мутации и ограничениях). Внешние источники не использовались.')
A(PageBreak())

H('1. Вариант и статус постановки')
P('<b>Важное уточнение:</b> согласно методичке номер индивидуального варианта вычисляется по N и Q, а для ЛР №2 допустимы только V=1,…,20. Эти N и Q не предоставлены. Число «22» в выражении d=5+(22 mod 6)=9 относится к размерности задачи ЛР №1, а не к определению варианта ЛР №2. Поэтому ЛР №2 выполнена как <b>демонстрационный V=3</b>, а не как официально установленный индивидуальный вариант.')
P('Точное название из методички: «Генетический алгоритм для дискретной задачи с ограничениями». Вариант V=3: «Рюкзак с обязательными и взаимоисключающими предметами». Основное представление — бинарная строка с жёсткими ограничениями (методичка, стр. 9).')
H('2. Цель и постановка задачи')
P('Цель из методички: научиться проектировать корректное дискретное представление решения, специальные генетические операторы и методы обработки ограничений на примере задачи выбора, распределения или планирования.')
P('Имеются 40 предметов, для каждого известны масса wᵢ и полезность vᵢ. Необходимо выбрать набор максимальной полезности, соблюдая вместимость рюкзака, обязательность некоторых предметов и несовместимость 24 пар предметов. Все данные синтетические и поставляются вместе с кодом.')
SH('2.1. Формальная модель')
A(formula('x = (x₁, ..., x₄₀),   xᵢ ∈ {0,1}'))
A(formula('max F(x) = Σᵢ vᵢ xᵢ'))
A(formula(f'Σᵢ wᵢ xᵢ ≤ W = {s["capacity"]} кг'))
A(formula('x₁ = x₂ = x₃ = 1'))
A(formula('x_a + x_b ≤ 1  для каждой конфликтующей пары (a,b) ∈ E'))
P('Бинарное значение xᵢ=1 означает включение предмета в рюкзак, xᵢ=0 — исключение. Генотип — массив из 40 битов; фенотип — выбранный набор предметов. Декодирование заключается в преобразовании единичных позиций в идентификаторы предметов.')

H('3. Исходные данные и ограничения')
P('Данные получены собственным генератором create_problem(seed=2026101802). Масса каждого предмета выбрана равномерно из целых значений 3…20 кг; полезность задана как vᵢ=3wᵢ+rᵢ, где rᵢ — целая псевдослучайная добавка 5…45. Обязательны предметы №1, №2 и №3. Конфликты — 24 различные случайные пары (за исключением пар между обязательными предметами). Вместимость: сумма масс обязательных предметов плюс 87 кг, то есть W=133 кг.')
P('Исключение конфликтов между обязательными объектами обеспечивает существование хотя бы одного допустимого решения. Исходные значения, seed и алгоритм генерации приложены; дополнительные данные из интернета не использовались.')
SH('3.1. Примеры допустимых и недопустимых решений')
exrows=[]
for e in s['examples']:
    codes=', '.join(map(str,e['items'][:17]))+('…' if len(e['items'])>17 else '')
    exrows.append((e['kind'],codes,f"{e['weight']} кг",e['value'],
                   'Да' if e['feasible'] else 'Нет',str(e['violation'])))
A(table(['Тип','Номера предметов','Масса','Польз.','Доп.','[m,c,e]'],exrows,
        widths=[110,185,50,42,38,75]))
P('В последнем столбце указаны: m — число пропущенных обязательных предметов, c — число конфликтующих выбранных пар, e — превышение вместимости в килограммах. Пример «нет обязательного» нарушает x₁=1; пример «конфликт» содержит несовместимые предметы №1 и №19; набор всех 40 предметов одновременно нарушает массу и конфликты.')

H('4. Модель и операторы генетического алгоритма')
SH('4.1. Инициализация и селекция')
P('Каждая из 48 стартовых хромосом формируется независимым включением каждого предмета с вероятностью 0,32. В режиме «ремонт» каждая хромосома сразу исправляется; в режиме «штраф» допускается присутствие недопустимых хромосом, а качество регулируется штрафной оценкой.')
P('Для выбора родителей используется турнир размером k=3: из текущей популяции с возвращением случайно выбираются три кандидата, родителем становится кандидат с максимальным значением используемого фитнеса. В качестве альтернативы рассмотрен в конспекте рулеточный отбор, однако выбран турнирный, потому что он корректно работает и для отрицательных штрафных оценок и не требует масштабирования.')
SH('4.2. Кроссовер, мутация, элитизм')
P('Рекомбинация — равномерный кроссовер с вероятностью Pc=0,88: для каждого бита выбирается ген одного из родителей, что позволяет комбинировать отдельные включённые предметы. Если кроссовер не применяется, потомки копируют родителей.')
P('Сравниваются два оператора мутации, при неизменной структуре алгоритма: (А) побитовая инверсия с вероятностью p=1/40 на каждом гене; (Б) обмен двух случайных позиций, выполняемый один раз на потомке. Обмен сохраняет количество единиц до коррекции ограничений; побитовая мутация может изменять это количество.')
P('Элитизм: в каждом поколении две наиболее приспособленные хромосомы переносятся без изменений. Однако глобально лучшее <b>допустимое</b> решение запоминается отдельно — «best-ever», в том числе при использовании штрафов.')
SH('4.3. Два подхода к ограничениям')
P('<b>Ремонт.</b> В хромосому принудительно включаются обязательные предметы; затем из несовместимой пары исключается необязательный предмет с меньшей полезностью на килограмм; далее, пока превышена масса, удаляется необязательный выбранный предмет с минимальным отношением полезности к массе. После такого ремонта полученная хромосома удовлетворяет всем ограничениям (при условии выполнимого обязательного набора).')
P('<b>Штрафы.</b> Исходная полезность корректируется штрафами за каждое нарушение. Это не гарантирует допустимость промежуточного поколения, поэтому итоговым ответом считается только лучшее допустимое решение, реально встретившееся во всех поколениях.')
A(formula('Fitness(x) = F(x) − 400m(x) − 250c(x) − 25e(x)'))
P('Где m — число пропущенных обязательных объектов, c — число выбранных конфликтных пар, e — превышение веса (кг). Коэффициенты — явно зафиксированные параметры эксперимента, а не теоретически оптимальные константы.')
P('Как отмечено в рукописном конспекте (лекция 4, стр. 26–30), бинарное кодирование удобно для задач выбора, но кроссовер и мутация могут порождать недопустимые хромосомы. Поэтому процедуры восстановления допустимости и явного учёта ограничений — обязательные части реализации.')

H('5. Вычислительная схема и конфигурация')
FIG('flowchart.png','Рисунок 1 — собственная схема цикла генетического алгоритма.',width=400)
SH('5.1. Параметры опытов')
params=[('Число объектов',40),('Размер популяции',48),('Поколения',120),
        ('Число элитных особей',2),('Турнир',3),('Pc',0.88),('p_mut', '1/40 на ген'),
        ('Тип кроссовера','Равномерный'),('Начальная вероятность бита 1',0.32),
        ('Критерий останова','120 поколений'),('Число независимых запусков на вариант',20),
        ('Общий бюджет оценок на запуск',s['budget_per_run']),
        ('Семена запусков','2026102000–2026102019'),('Seed данных','2026101802')]
A(table(['Параметр','Значение'],params,widths=[275,225]))
P('Оценивались 48 стартовых особей и 46 новых потомков в каждом из следующих 119 поколений: B = 48 + 119·46 = 5 522. Элитные особи используют сохранённые значения фитнеса и не переоцениваются. Для случайного поиска сформировано ровно B новых кандидатов.')
P('Фиксированные seed позволяют воспроизвести результаты. Все четыре конфигурации использовали одинаковый список из 20 seed. Сравнения попарно изменяли ровно один фактор: «ремонт/bitflip» vs «штраф/bitflip» — только обработка ограничений; «ремонт/bitflip» vs «ремонт/swap» — только мутация.')

H('6. Экспериментальные результаты')
statrows=[]
for k,d in s['statistics'].items():
    statrows.append([k,d['best'],f"{d['mean']:.2f}",f"{d['median']:.1f}",
                     f"{d['std_sample']:.2f}",d['worst'],f"{d['mean_feasible_rate']*100:.1f}%"])
A(table(['Конфигурация','Лучшее','Среднее','Медиана','σ','Худшее','Допуст.'],statrows,
        widths=[178,51,56,54,42,51,68]))
P('Показаны распределения лучших допустимых значений 20 независимых запусков каждого метода. Стандартное отклонение является выборочным (ddof=1). Для решения о качестве важны и медиана, и худший результат: одиночный удачный запуск не гарантирует устойчивости.')
SH('6.1. Анализ влияния обработки ограничений')
P('При побитовой мутации ремонт дал среднее 810,15 и медиану 811, тогда как штрафной подход — среднее 794,65 и медиану 796. Доля допустимых оцененных хромосом: 100% против примерно 39,7%. Прямой ремонт оказал положительное влияние в этой конкретной синтетической задаче, но он также уменьшает исследуемое пространство и может мешать в других задачах.')
SH('6.2. Анализ оператора мутации')
P('При одинаковой процедуре ремонта побитовая мутация дала среднее 810,15 против 807,05 для обмена двух позиций. Это согласуется с тем, что простой обмен сохраняет число выбранных предметов и может хуже исследовать комбинации разной мощности; после ремонта это свойство частично нарушается. Вывод относится к выбранным настройкам и синтетическим данным.')
SH('6.3. Сравнение с базовыми методами')
P('Случайный допустимый поиск при том же бюджете показал среднее 788,50 и медиану 786,5 — хуже рассматриваемых ГА, но также нашёл лучший результат 811 хотя бы в одном запуске. Отдельная жадная эвристика по отношению полезность/масса также достигла 811. Следовательно, для данного экземпляра <b>не доказано преимущество ГА над конструктивной жадной эвристикой</b>; сравнение с ней приведено без искусственного завышения результата ГА.')

H('7. Графики и интерпретация')
FIG('convergence.png','Рисунок 2 — средние траектории лучшего допустимого значения по поколениям.',width=492)
FIG('boxplot.png','Рисунок 3 — разброс итоговых результатов по 20 запускам.',width=492)
FIG('feasible_rate.png','Рисунок 4 — сравнение доли допустимых кандидатов.',width=492)
P('При использовании штрафов недопустимые особи могут сохраняться в популяции и влиять на отбор. Однако графики измеряют только качество лучшего <b>допустимого</b> найденного решения; смешивать его со штрафным фитнесом некорректно. Для случайного поиска «поколение» обозначает эквивалентную партию оценок, а не эволюционный шаг.')

H('8. Лучшее найденное решение')
sol=s['best_overall'];P(f'Лучший найденный допустимый комплект содержит {len(sol["items_1based"])} предметов: {", ".join(map(str,sol["items_1based"]))}.')
P(f'Полезность = <b>{sol["value"]}</b>, масса = <b>{sol["weight"]} кг</b> из {s["capacity"]} кг, seed = <b>{sol["seed"]}</b>, конфигурация: {sol["configuration"]}.')
soltable=[]
for i in sol['items_1based']:
    r=items[i-1]
    soltable.append([i,r['weight_kg'],r['utility_points'],'Да' if r['mandatory']=='1' else 'Нет'])
A(table(['№ предмета','Масса, кг','Полезность','Обязательный'],soltable,widths=[115,125,130,130]))
P('Контроль допустимости лучшего решения: отсутствующие обязательные предметы — 0; конфликтные выбранные пары — 0; превышение вместимости — 0. Проверки выполнены программно и сохранены в summary.json.')
P('Значение 811 — лучшее из наблюдавшихся при указанном конечном бюджете, <b>не доказанный глобальный оптимум</b>. Для строгого доказательства оптимальности необходим исчерпывающий перебор с отсечениями либо точный алгоритм (в задаче с 40 двоичными переменными это потенциально существенно дороже).')

H('9. Ограничения эксперимента и заключение')
P('Задача достаточно дискретна и нелинейна по допустимому множеству: обязательные предметы и конфликты запрещают многие сочетания. Бинарная популяция обоснованна, поскольку единичный бит имеет прямой предметный смысл. Равномерное скрещивание и две мутации специально работают с бинарной хромосомой; их результат может быть недопустим, что продемонстрировано и обрабатывается двумя исследованными методами.')
P('Качество ГА «ремонт / bitflip» в данном эксперименте хорошее относительно равнобюджетного случайного поиска, прежде всего из-за высокой устойчивости. Но так как жадная эвристика тоже находит 811, нельзя делать вывод, что эволюционный поиск необходим для этого конкретного экземпляра. Дополнительная проверка на разных экземплярах и более сложных конфликтах улучшила бы обобщаемость результатов.')
P('Вычислительный бюджет измеряется числом вызовов исходной функции полезности; стоимость самого ремонта в этот бюджет не входит. Поэтому время исполнения алгоритмов не обязано быть одинаковым. Коэффициенты штрафов и частоты мутаций эмпирические и могут потребовать перенастройки на других данных.')
P('Результаты ограничены 20 seed и одним синтетическим набором из 40 предметов. Статистическое сравнение не заменяет строгого доказательства оптимальности. Код проверен автоматическими тестами (12 тестов).')

H('10. Как воспроизвести результаты')
A(para('Пример запуска из каталога лабораторной работы:',BODY))
A(Preformatted('python -m pip install -r requirements.txt\npython main.py --out results --runs 20 --seed-base 2026102000\npython -m unittest -v test_lab2.py',CODE))
P('Устанавливать готовые библиотеки эволюционной оптимизации не требуется; генетические операторы реализованы вручную. В архив включены main.py, test_lab2.py, README.md, requirements.txt, requirements-lock.txt, файл генерации PDF, входные данные, таблицы, 4 диаграммы и протокол тестов.')
P('Независимые запуски: runs.csv содержит seed, лучшую допустимую полезность, массу, число оценок и выбранные предметы; trajectories.csv — значения по поколениям. Параметры сохранены в config.json, данные — в items.csv, conflicts.csv, instance.json.')

H('Приложение А. Полная таблица объектов')
A(table(['Предмет','Масса, кг','Полезность','Обязательный'],
        [(r['item_id'],r['weight_kg'],r['utility_points'],'Да' if r['mandatory']=='1' else 'Нет') for r in items],
        widths=[120,120,130,130]))
SH('Полный список конфликтных пар')
conflicts=s['conflicts_1based']
C=[]
for i in range(0,len(conflicts),4):
    C.append([f'{a}–{b}' if a is not None else '' for a,b in conflicts[i:i+4]]+['']*(4-len(conflicts[i:i+4])))
A(table(['Пара 1','Пара 2','Пара 3','Пара 4'],C,widths=[125]*4))

H('Приложение Б. Индивидуальные результаты 80 запусков')
run_table=[]
for idx,r in enumerate(rows):
    names={'ГА: ремонт / bitflip':'R/B','ГА: штраф / bitflip':'P/B',
           'ГА: ремонт / swap':'R/S','Случайный допустимый':'RAND'}
    run_table.append([names[r['configuration']],r['seed'],r['best_feasible_utility'],
                      r['weight_kg'],r['feasible_rate'][:7],r['evaluations']])
A(table(['Алгоритм','Seed','Лучшая польз.','Масса','Доля доп.','Оценок'],
        run_table,widths=[80,100,100,75,75,70]))
P('Обозначения: R/B — repair + bitflip; P/B — penalty + bitflip; R/S — repair + swap; RAND — случайный допустимый поиск. Полные траектории и хромосомы — в машиночитаемых CSV архива.')

H('Приложение В. Существенные фрагменты кода')
P('Ниже приводятся основные операции из запускаемой программы. Полные исходники доступны в ZIP и являются частью сдаваемого результата.')
code_snips=[
('Проверка ограничений и их ремонт', '''def violation(x, p):
    missing = sum(1 for i in p.mandatory if not x[i])
    conflicts = sum(1 for i, j in p.conflicts
                    if x[i] and x[j])
    excess = max(0, used_weight(x, p) - p.capacity)
    return missing, conflicts, excess

# Полный repair() см. в main.py.
'''),
('Бинарная рекомбинация и мутация', '''def crossover(a, b, rng, p_cross):
    if rng.random() >= p_cross:
        return a.copy(), b.copy()
    mask = rng.random(len(a)) < .5
    return (np.where(mask, a, b).copy(),
            np.where(mask, b, a).copy())

def mutate(x, rng, mode, p_gene):
    y = x.copy()
    if mode == 'bitflip':
        mask = rng.random(len(y)) < p_gene
        y[mask] = ~y[mask]
    elif mode == 'swap':
        if rng.random() < min(1.0, p_gene * len(y)):
            i, j = rng.choice(len(y), size=2, replace=False)
            y[i], y[j] = y[j], y[i]
    return y
'''),
('Точный бюджет оценок', '''@property
 def budget(self) -> int:
     return self.population + (
         self.generations - 1
     ) * (self.population - self.elite)

# В данной конфигурации: 48 + 119 * 46 = 5522.
''')]
for name,code in code_snips:
    SH(name)
    lines=[]
    for line in code.splitlines():
        if len(line)>78:
            lines.extend(textwrap.wrap(line,78,subsequent_indent='    '))
        else:lines.append(line)
    A(Preformatted('\n'.join(lines),CODE))
    A(Spacer(1,8))

H('Источники и использованные материалы')
RAW('1. Душкин Р. В. «Эволюционное программирование и генетические алгоритмы». Комплекс лабораторных работ. Стр. 2–3, 8–12 (источник постановки, минимальных масштабов, требований к экспериментам и операторов).')
RAW('2. Фотографии рукописных конспектов: лекция 1–2 (базовый эволюционный цикл и статистика), лекция 4, стр. 25–30 (бинарное кодирование, селекция, кроссовер, мутация, обработка ограничений).')
RAW('3. Собственные синтетические данные, Python-код, тесты и результаты запусков; seed и структура генератора указаны выше. Внешние интернет-источники не привлекались.')

Report(str(OUT),title='Лабораторная работа №2',author='').multiBuild(story)
print(OUT)
