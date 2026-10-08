from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from pathlib import Path

OUT = Path.cwd() / 'Документы проекта'
OUT.mkdir(exist_ok=True)

NAVY = '1F4E79'
LIGHT_BLUE = 'D9EAF7'
BORDER = 'D9D9D9'

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), color); tcPr.append(shd)

def borders(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in('w:tcBorders')
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders'); tcPr.append(tcBorders)
    for edge in ('top','left','bottom','right','insideH','insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'),'single'); el.set(qn('w:sz'),'6'); el.set(qn('w:color'), BORDER)
        tcBorders.append(el)

def set_cell_text(cell, text, bold=False, color=None):
    cell.text = ''
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.space_before = Pt(3)
    r = p.add_run(text); r.bold = bold; r.font.size = Pt(9)
    if color: r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    borders(cell)

def table(doc, headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = 'Table Grid'
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; shade(c,NAVY); set_cell_text(c,h,True,'FFFFFF')
    for ri,row in enumerate(rows):
        cells=t.add_row().cells
        for i,val in enumerate(row):
            if ri%2: shade(cells[i],'F4F8FB')
            set_cell_text(cells[i],str(val))
    if widths:
        for row in t.rows:
            for i,w in enumerate(widths): row.cells[i].width=Cm(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return t

def setup(doc):
    sec=doc.sections[0]
    sec.top_margin=Cm(2); sec.bottom_margin=Cm(2); sec.left_margin=Cm(2.2); sec.right_margin=Cm(2.0)
    styles=doc.styles
    normal=styles['Normal']; normal.font.name='Arial'; normal._element.rPr.rFonts.set(qn('w:ascii'),'Arial'); normal._element.rPr.rFonts.set(qn('w:hAnsi'),'Arial'); normal.font.size=Pt(11)
    normal.paragraph_format.space_after=Pt(6); normal.paragraph_format.line_spacing=1.15
    for name,size in [('Title',22),('Heading 1',15),('Heading 2',12)]:
        s=styles[name]; s.font.name='Arial'; s._element.rPr.rFonts.set(qn('w:ascii'),'Arial'); s._element.rPr.rFonts.set(qn('w:hAnsi'),'Arial'); s.font.size=Pt(size); s.font.bold=True; s.font.color.rgb=RGBColor(0,0,0)
        s.paragraph_format.space_before=Pt(16 if name!='Title' else 0); s.paragraph_format.space_after=Pt(8)
    footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('Веб витрина онлайн магазина | Учебный проект').font.size=Pt(8)

def title_page(doc, title, role):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(95)
    r=p.add_run('УЧЕБНЫЙ ПРОЕКТ'); r.bold=True; r.font.size=Pt(14)
    p=doc.add_paragraph(style='Title'); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(title)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run('Технический отчёт и план реализации'); r.font.size=Pt(13)
    doc.add_paragraph().paragraph_format.space_after=Pt(70)
    for label,value in [('Роль в команде',role),('Проект','Веб витрина онлайн магазина'),('Технологический стек','React, FastAPI, SQLite или PostgreSQL, GitHub')]:
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(label+': ').bold=True; p.add_run(value)
    doc.add_page_break()

def intro(doc, role, purpose):
    doc.add_heading('1 Общая характеристика проекта',1)
    doc.add_paragraph('Проект представляет собой веб витрину онлайн магазина. Пользователь сможет просматривать каталог, находить товары через поиск и фильтры, открывать карточку товара, добавлять позиции в корзину и оформлять тестовый заказ. Работа ведётся в команде из двух разработчиков: frontend разработчик отвечает за клиентскую часть и пользовательский интерфейс, backend разработчик отвечает за серверную часть, API, хранение данных и авторизацию.')
    doc.add_paragraph(f'Цель настоящего отчёта - зафиксировать задачи {role}, ожидаемый результат работы, порядок взаимодействия с другим участником команды и критерии готовности. {purpose}')
    doc.add_heading('2 Концепция и границы проекта',1)
    doc.add_paragraph('Магазин не является полноценной платёжной системой. Оформление заказа носит демонстрационный характер: пользователь вводит контактные данные, после чего заказ сохраняется со статусом «Новый». Это позволяет сосредоточиться на учебных целях: разработке современного интерфейса, REST API, базе данных, авторизации и совместной работе с GitHub.')
    table(doc,['Версия','Содержание','Результат'],[
        ['Версия 1','Каталог без базы данных, данные из JSON или временного массива','Работает просмотр каталога и карточек товаров'],
        ['Версия 2','Подключение базы данных, товары, категории, корзина и заказы','Данные сохраняются и выдаются через API'],
        ['Версия 3','Регистрация, вход, JWT токен, роли user и admin','Корзина и заказы привязаны к пользователю']
    ],[2.2,8.2,5.2])

def github(doc):
    doc.add_heading('Взаимодействие через GitHub',2)
    doc.add_paragraph('В репозитории создаются ветки main, develop, frontend и backend. В main попадает только проверенная версия. Каждый участник выполняет задачи в своей ветке, делает небольшие осмысленные коммиты и создаёт Pull Request для объединения изменений. В README размещаются описание проекта, инструкция запуска, список технологий, структура каталогов и скриншоты интерфейса.')

def frontend():
    d=Document(); setup(d); title_page(d,'Отчёт frontend разработчика','Frontend разработчик и дизайнер интерфейса')
    intro(d,'frontend разработчика','Документ является основой для реализации клиентской части и её проверки на защите проекта.')
    d.add_heading('3 Обязанности frontend разработчика',1)
    table(d,['Направление','Задачи','Готовый результат'],[
        ['Интерфейс','Создать единый стиль, шапку сайта, навигацию, карточки товаров, формы и сообщения','Понятный адаптивный интерфейс'],
        ['Страницы','Сверстать главную, каталог, карточку товара, корзину, вход, регистрацию и оформление заказа','Все пользовательские сценарии доступны'],
        ['Интеграция','Отправлять запросы к FastAPI, отображать данные, ошибки и загрузку','Интерфейс использует реальный API'],
        ['Качество','Проверить адаптивность, валидацию форм и работу в браузере','Нет критических ошибок в сценариях']
    ],[3.0,8.2,4.4])
    d.add_heading('4 Техническое задание на клиентскую часть',1)
    d.add_heading('4.1 Структура интерфейсов',2)
    table(d,['Страница','Элементы интерфейса','Действие пользователя'],[
        ['Главная','Шапка, баннер, категории, популярные товары','Переходит в каталог или открывает товар'],
        ['Каталог','Карточки, поиск, фильтр категории и цены, сортировка','Находит нужный товар'],
        ['Карточка товара','Фото, название, цена, описание, остаток, кнопка добавления','Добавляет товар в корзину'],
        ['Корзина','Список позиций, количество, удаление, итоговая сумма','Изменяет состав заказа'],
        ['Вход и регистрация','Поля формы, валидация, уведомления','Создаёт аккаунт или входит'],
        ['Оформление заказа','Контактные данные, состав заказа, подтверждение','Создаёт тестовый заказ'],
        ['Администрирование','Таблица товаров, форма добавления и редактирования','Управляет каталогом при роли admin']
    ],[3.0,7.3,5.3])
    d.add_heading('4.2 Пользовательские пути',2)
    d.add_paragraph('Гость: главная страница -> каталог -> фильтрация или поиск -> карточка товара -> корзина. Для создания заказа гость переходит к регистрации или входу.')
    d.add_paragraph('Пользователь: вход -> каталог -> карточка товара -> добавление в корзину -> оформление -> страница подтверждения. Администратор: вход -> административная страница -> создание, редактирование или удаление товара.')
    d.add_heading('4.3 Компоненты и структура клиентской части',2)
    table(d,['Каталог','Назначение'],[
        ['pages','Композиция страниц приложения'],['components','Переиспользуемые элементы: Header, ProductCard, Search, Filter, CartItem, Loader'],['services','Функции запросов к API и обработка токена'],['store или context','Состояние корзины, пользователя и уведомлений'],['styles','Глобальные стили, адаптивные правила и переменные оформления']
    ],[4.5,11.1])
    d.add_page_break()
    d.add_heading('5 План работ frontend разработчика',1)
    table(d,['Этап','Задачи','Критерий завершения'],[
        ['1. Подготовка','Создать React проект, настроить маршрутизацию, базовые стили и ветку frontend','Проект запускается локально'],
        ['2. Макет','Собрать каркас всех страниц и мобильную версию','Можно пройти по всем экранам'],
        ['3. Каталог','Вывести товары из API, добавить поиск, фильтры и сортировку','Каталог реагирует на действия пользователя'],
        ['4. Корзина','Добавление, изменение количества, удаление, расчёт итоговой суммы','Корзина корректно пересчитывается'],
        ['5. Аккаунт','Формы регистрации и входа, хранение токена, защита страниц','Пользователь входит и остаётся авторизованным'],
        ['6. Проверка','Тестировать основные пути, исправить ошибки, оформить README','Клиентская часть готова к демонстрации']
    ],[3.0,8.2,4.4])
    d.add_heading('6 Контракт взаимодействия с backend',1)
    d.add_paragraph('Frontend не обращается к базе данных напрямую. Все данные получаются через REST API. Для запросов используются единые функции сервиса. При авторизации токен JWT передаётся в заголовке Authorization: Bearer <token>. Backend заранее предоставляет адрес API, структуру ответов, перечень возможных ошибок и тестовые данные.')
    table(d,['Данные от backend','Как используются на клиенте'],[
        ['GET /products','Отображение каталога и поиска'],['GET /products/{id}','Карточка выбранного товара'],['POST /auth/register и /auth/login','Создание аккаунта и вход'],['GET и POST /cart','Отображение и изменение корзины'],['POST /orders','Подтверждение оформления заказа']
    ],[6.0,9.6])
    d.add_heading('7 Критерии приёмки клиентской части',1)
    d.add_paragraph('Интерфейс корректно отображается на экранах шириной от 360 пикселей. Все страницы доступны через маршруты. Товары загружаются с API, а состояние загрузки и ошибки понятны пользователю. Формы не отправляются при пустых или неверно заполненных обязательных полях. Корзина корректно показывает позиции и итоговую стоимость. После входа пользователь видит состояние авторизации, а функции администратора не отображаются обычному пользователю.')
    github(d)
    d.add_heading('8 Итог',1)
    d.add_paragraph('Результатом работы frontend разработчика является удобная веб витрина, соединённая с серверной частью. Пользователь должен пройти полный демонстрационный путь от поиска товара до создания заказа без необходимости работать с техническими инструментами.')
    d.save(OUT/'Отчет frontend разработчика веб витрина.docx')

def backend():
    d=Document(); setup(d); title_page(d,'Отчёт backend разработчика','Backend разработчик и архитектор базы данных')
    intro(d,'backend разработчика','Документ определяет архитектуру серверной части, API, модель данных и последовательность реализации.')
    d.add_page_break()
    d.add_heading('3 Архитектурное решение',1)
    d.add_paragraph('Для серверной части выбран FastAPI. Фреймворк подходит для учебного проекта благодаря высокой скорости разработки, встроенной документации Swagger, удобной валидации входных данных и ясному описанию REST API. Сервер принимает запросы от React приложения, выполняет проверку данных, обращается к базе данных и возвращает ответы в формате JSON.')
    table(d,['Слой','Назначение','Примеры'],[
        ['API роуты','Принимают HTTP запросы и возвращают ответы','products, auth, cart, orders'],
        ['Сервисы','Содержат бизнес логику','Расчёт суммы заказа, проверка прав'],
        ['Схемы','Проверяют входные и выходные данные','ProductCreate, UserLogin, OrderResponse'],
        ['Модели БД','Описывают таблицы и связи','User, Product, Category, Order'],
        ['Хранилище','Сохраняет данные','SQLite на разработке, PostgreSQL при развёртывании']
    ],[3.0,6.1,6.5])
    d.add_heading('4 Техническое задание на серверную часть',1)
    d.add_heading('4.1 Функциональные требования',2)
    table(d,['Модуль','Функционал'],[
        ['Каталог','Выдача товаров, получение товара по идентификатору, поиск, фильтрация и сортировка'],
        ['Управление товарами','Создание, изменение и удаление товара только администратором'],
        ['Пользователи','Регистрация, безопасное хранение хеша пароля, вход в систему'],
        ['Авторизация','Выдача и проверка JWT токена, разграничение ролей user и admin'],
        ['Корзина','Добавление товаров, изменение количества, удаление позиции, подсчёт стоимости'],
        ['Заказы','Проверка корзины, сохранение заказа и позиций заказа, выдача истории заказов']
    ],[4.0,11.6])
    d.add_heading('4.2 REST API',2)
    table(d,['Метод','Маршрут','Назначение','Доступ'],[
        ['GET','/products','Список товаров с параметрами поиска и фильтра','Все'],['GET','/products/{id}','Карточка товара','Все'],['POST','/products','Создание товара','admin'],['PUT','/products/{id}','Редактирование товара','admin'],['DELETE','/products/{id}','Удаление товара','admin'],['POST','/auth/register','Регистрация пользователя','Все'],['POST','/auth/login','Вход и выдача JWT','Все'],['GET','/cart','Получение корзины','user'],['POST','/cart/items','Добавление позиции','user'],['PUT','/cart/items/{id}','Изменение количества','user'],['DELETE','/cart/items/{id}','Удаление позиции','user'],['POST','/orders','Оформление заказа','user'],['GET','/orders','История заказов','user']
    ],[1.4,4.2,7.3,2.7])
    d.add_heading('5 Структура базы данных',1)
    d.add_paragraph('Для второй и третьей версий используется реляционная база данных. Основные связи: одна категория включает много товаров; пользователь имеет одну корзину и много заказов; заказ содержит одну или несколько позиций; каждая позиция ссылается на товар.')
    table(d,['Таблица','Ключевые поля','Назначение'],[
        ['users','id, name, email, password_hash, role','Учётные записи и роли'],['categories','id, name','Группы товаров'],['products','id, category_id, name, price, stock','Карточки товаров'],['carts','id, user_id','Корзина пользователя'],['cart_items','id, cart_id, product_id, quantity','Содержимое корзины'],['orders','id, user_id, total_price, status, created_at','Оформленные заказы'],['order_items','id, order_id, product_id, price, quantity','Состав заказа']
    ],[3.3,7.2,5.1])
    d.add_heading('5.1 Пример SQL схемы',2)
    sql='''CREATE TABLE users (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name VARCHAR(100) NOT NULL,\n    email VARCHAR(150) UNIQUE NOT NULL,\n    password_hash VARCHAR(255) NOT NULL,\n    role VARCHAR(20) NOT NULL DEFAULT 'user'\n);\n\nCREATE TABLE products (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    category_id INTEGER NOT NULL,\n    name VARCHAR(150) NOT NULL,\n    description TEXT,\n    price DECIMAL(10, 2) NOT NULL,\n    image_url VARCHAR(255),\n    stock INTEGER NOT NULL DEFAULT 0,\n    FOREIGN KEY (category_id) REFERENCES categories(id)\n);\n\nCREATE TABLE orders (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    user_id INTEGER NOT NULL,\n    total_price DECIMAL(10, 2) NOT NULL,\n    status VARCHAR(30) NOT NULL DEFAULT 'new',\n    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,\n    FOREIGN KEY (user_id) REFERENCES users(id)\n);'''
    p=d.add_paragraph(); r=p.add_run(sql); r.font.name='Consolas'; r._element.rPr.rFonts.set(qn('w:ascii'),'Consolas'); r.font.size=Pt(8)
    d.add_heading('6 План работ backend разработчика',1)
    table(d,['Этап','Задачи','Критерий завершения'],[
        ['1. Основа','Создать FastAPI проект, конфигурацию, структуру модулей и Swagger','Сервер запускается, /docs доступен'],['2. Версия без БД','Подготовить временный источник товаров и методы GET /products','Каталог получает тестовые товары'],['3. База данных','Создать модели, миграции, CRUD товаров и категорий','Товары сохраняются в БД'],['4. Корзина и заказы','Добавить сервис корзины, расчёт суммы, создание заказа','Заказ создаётся из корзины'],['5. Авторизация','Регистрация, хеширование пароля, JWT, роли','Маршруты защищены правами'],['6. Качество','Тесты API, обработка ошибок, CORS, README','API готов к интеграции и демонстрации']
    ],[3.0,8.2,4.4])
    d.add_heading('7 Требования безопасности и качества',1)
    d.add_paragraph('Пароли не хранятся в открытом виде: используется хеширование. JWT имеет ограниченный срок действия. Маршруты изменения каталога проверяют роль администратора. Сервер валидирует типы данных, не допускает отрицательную цену или количество товара и возвращает понятные HTTP статусы: 400 для неверных данных, 401 для неавторизованного пользователя, 403 для недостаточных прав и 404 для отсутствующего объекта. CORS настраивается только для адреса клиентского приложения.')
    d.add_heading('8 Взаимодействие с frontend разработчиком',1)
    d.add_paragraph('До начала интеграции backend разработчик фиксирует примеры запросов и ответов в Swagger. Изменения контрактов API согласуются заранее. Для frontend предоставляются тестовые товары, учётная запись администратора и сценарии проверки: просмотр каталога, вход, работа с корзиной и создание заказа. Ошибки интеграции фиксируются в GitHub Issues.')
    d.add_page_break()
    github(d)
    d.add_heading('9 Итог',1)
    d.add_paragraph('Результатом работы backend разработчика является документированный REST API на FastAPI, база данных с понятной структурой и безопасная авторизация. Серверная часть обеспечивает сохранность данных и поддерживает все функции, доступные пользователю в веб интерфейсе.')
    d.save(OUT/'Отчет backend разработчика веб витрина.docx')

frontend(); backend()
