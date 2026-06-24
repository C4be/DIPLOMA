# Схема базы данных авиакомпании

## Таблица Bookings (Бронирования)
- **book_ref** — первичный ключ
- **book_date**
- **total_amount**

## Таблица Tickets (Билеты)
- **ticket_no** — первичный ключ
- **book_ref** — внешний ключ → Bookings.book_ref
- **passenger_id**
- **passenger_name**
- **outbound**

## Таблица Segments (Перелеты)
- **ticket_no** — часть составного первичного ключа
- **flight_id** — часть составного первичного ключа + внешний ключ → Flights.flight_id
- **fare_conditions**
- **price**

## Таблица Boarding_passes (Посадочные талоны)
- **ticket_no** — часть составного первичного ключа
- **flight_id** — часть составного первичного ключа + внешний ключ → Flights.flight_id
- **seat_no**
- **boarding_no** (nullable)
- **boarding_time** (nullable)

## Таблица Routes (Маршруты)
- **route_no** — часть составного первичного ключа
- **validity** — часть составного первичного ключа
- **departure_airport** — внешний ключ → Airports.airport_code
- **arrival_airport** — внешний ключ → Airports.airport_code
- **airplane_code** — внешний ключ → Airplanes.airplane_code
- **days_of_week**
- **scheduled_time**
- **duration**

## Таблица Flights (Рейсы)
- **flight_id** — первичный ключ
- **route_no** — внешний ключ → Routes.route_no
- **status**
- **scheduled_departure**
- **scheduled_arrival**
- **actual_departure** (nullable)
- **actual_arrival** (nullable)

## Таблица Airports (Аэропорты)
- **airport_code** — первичный ключ
- **airport_name**
- **city**
- **country**
- **coordinates**
- **timezone**

## Таблица Airplanes (Самолеты)
- **airplane_code** — первичный ключ
- **model**
- **range**
- **speed**

## Таблица Seats (Места)
- **airplane_code** — часть составного первичного ключа + внешний ключ → Airplanes.airplane_code
- **seat_no** — часть составного первичного ключа
- **fare_conditions**

# Связи между таблицами (Foreign Keys + cardinality)

1. **Bookings → Tickets**
   Bookings (1) ── (N) Tickets
   Ключ: Tickets.book_ref = Bookings.book_ref

2. **Tickets → Segments**
   Tickets (1) ── (N) Segments
   Ключ: Segments.ticket_no = Tickets.ticket_no

3. **Flights → Segments**
   Flights (1) ── (N) Segments
   Ключ: Segments.flight_id = Flights.flight_id

4. **Routes → Flights**
   Routes (1) ── (N) Flights
   Ключ: Flights.route_no = Routes.route_no

5. **Airports → Routes** (два направления)
   Airports (1) ── (N) Routes (departure)
   Airports (1) ── (N) Routes (arrival)
   Ключи: Routes.departure_airport = Airports.airport_code
          Routes.arrival_airport   = Airports.airport_code

6. **Airplanes → Routes**
   Airplanes (1) ── (N) Routes
   Ключ: Routes.airplane_code = Airplanes.airplane_code

7. **Tickets → Boarding_passes**
   Tickets (1) ── (N) Boarding_passes
   Ключ: Boarding_passes.ticket_no = Tickets.ticket_no

8. **Flights → Boarding_passes**
   Flights (1) ── (N) Boarding_passes
   Ключ: Boarding_passes.flight_id = Flights.flight_id

9. **Airplanes → Seats**
   Airplanes (1) ── (N) Seats
   Ключ: Seats.airplane_code = Airplanes.airplane_code

10. **Неявная связь Boarding_passes ↔ Seats**
    Чтобы узнать, на каком самолёте место seat_no, нужно идти:
    Boarding_passes.flight_id → Flights.route_no → Routes.airplane_code → Seats.airplane_code + seat_no

# Дополнительные бизнес-связи (для понимания)
- fare_conditions присутствует и в Segments, и в Seats → это класс обслуживания (Economy, Business, Comfort).
- Один билет (Tickets) может содержать несколько сегментов (Segments) — это перелёты с пересадками.
- Boarding_passes выдаётся только на конкретный рейс (flight_id) и место (seat_no).

Основной сущностью является бронирование (bookings).

В одно бронирование можно включить несколько пассажиров, каждому из которых выписывается билет (tickets) на поездку в прямом направлении, а также отдельный обратный билет, если билеты приобретаются «туда и обратно». Билет имеет уникальный номер и содержит информацию о пассажире. Для пассажира нет отдельной сущности, но можно считать, что номер документа уникально идентифицирует пассажира.

Билет включает один перелет (segment), если между пунктами отправления и назначения есть прямой рейс, и несколько перелетов, если требуются пересадки. Все билеты в одном бронировании имеют одинаковый набор перелетов, хотя в схеме данных такого ограничения нет.

Маршруты (routes) проложены из одного аэропорта (airports) в другой. Каждый рейс (flights) следует по определенному маршруту, так что рейсы с одним номером маршрута имеют одинаковые пункты вылета и назначения, но отличаются датой отправления.

Маршрутная сеть меняется раз в месяц, поэтому рейсы и маршруты связаны темпоральным внешним ключом: при соединении следует учитывать не только номер маршрута, но и соответствие времени отправления интервалу действия маршрута. Для упрощения запросов можно использовать представление timetable, скрывающее соединение этих таблиц.

Все перелеты считаются стыковочными: пассажир проходит регистрацию на первый рейс и сразу получает посадочные талоны (boarding_passes) на все рейсы в своем билете. В посадочном талоне указано место, а также фиксируется время посадки в самолёт. Пассажир может зарегистрироваться только на тот рейс, который есть у него в билете. Комбинация рейса и места в самолёте уникальна, чтобы не допустить выдачу двух посадочных талонов на одно место.

Количество мест (seats) в самолёте и их распределение по классам обслуживания зависит от модели самолёта (airplanes), выполняющего рейс. Предполагается, что каждая модель самолёта имеет только одну компоновку салона. Схема данных не контролирует, что места в посадочных талонах соответствуют имеющимся в самолёте (такая проверка может быть сделана с использованием табличных триггеров или в приложении).

# Схема базы данных bookings — демонстрационная база авиакомпании

## Объекты схемы bookings

| Имя                     | Тип            | Описание                          |
|-------------------------|----------------|-----------------------------------|
| airplanes               | представление  | Самолёты                          |
| airplanes_data          | таблица        | Самолёты (переводы)               |
| airports                | представление  | Аэропорты                         |
| airports_data           | таблица        | Аэропорты (переводы)              |
| boarding_passes         | таблица        | Посадочные талоны                 |
| bookings                | таблица        | Бронирования                      |
| flights                 | таблица        | Рейсы                             |
| flights_flight_id_seq   | последовательность |                                   |
| routes                  | таблица        | Маршруты                          |
| seats                   | таблица        | Места                             |
| segments                | таблица        | Перелёты                          |
| tickets                 | таблица        | Билеты                            |
| timetable               | представление  | Расписание                        |

search_path по умолчанию: bookings, "$user", public
Для функций bookings.now() и bookings.version() схему указывать обязательно.

## Таблица / представление airplanes

**airplanes** — представление
**airplanes_data** — базовая таблица (jsonb-переводы)

### Поля представления airplanes
- airplane_code    char(3)     — код ИАТА самолёта (PK)
- model            text        — название модели (зависит от bookings.lang)
- range            integer     — максимальная дальность, км (> 0)
- speed            integer     — крейсерская скорость, км/ч (> 0)

### Базовая таблица airplanes_data
- airplane_code    char(3)     PK
- model            jsonb       NOT NULL
- range            integer     NOT NULL CHECK (> 0)
- speed            integer     NOT NULL CHECK (> 0)

Ссылки на airplanes_data:
- routes.airplane_code
- seats.airplane_code (ON DELETE CASCADE)

## Таблица / представление airports

**airports** — представление
**airports_data** — базовая таблица (jsonb-переводы)

### Поля представления airports
- airport_code     char(3)     — код ИАТА аэропорта (PK)
- airport_name     text        — название (зависит от lang)
- city             text        — город (зависит от lang)
- country          text        — страна (зависит от lang)
- coordinates      point       — долгота, широта
- timezone         text        — часовой пояс

### Базовая таблица airports_data
- airport_code     char(3)     PK
- airport_name     jsonb       NOT NULL
- city             jsonb       NOT NULL
- country          jsonb       NOT NULL
- coordinates      point       NOT NULL
- timezone         text        NOT NULL

Ссылки на airports_data:
- routes.departure_airport
- routes.arrival_airport

## Таблица bookings.bookings

- book_ref        char(6)         PK
- book_date       timestamptz     NOT NULL
- total_amount    numeric(10,2)   NOT NULL

Ссылки на bookings:
- tickets.book_ref

## Таблица bookings.tickets

- ticket_no       text        PK              (13 цифр)
- book_ref        char(6)     NOT NULL
- passenger_id    text        NOT NULL
- passenger_name  text        NOT NULL
- outbound        boolean     NOT NULL        (туда / обратно)

Уникальность: (book_ref, passenger_id, outbound)

Ссылки на tickets:
- segments.ticket_no

## Таблица bookings.segments

- ticket_no       text          PK (вместе с flight_id)
- flight_id       integer       PK (вместе с ticket_no)
- fare_conditions text          NOT NULL  (Economy / Comfort / Business)
- price           numeric(10,2) NOT NULL  (>= 0)

Ссылки:
- tickets.ticket_no
- flights.flight_id

Ссылки на segments:
- boarding_passes (ticket_no, flight_id)

## Таблица bookings.boarding_passes

- ticket_no       text        PK (вместе с flight_id)
- flight_id       integer     PK (вместе с ticket_no)
- seat_no         text        NOT NULL
- boarding_no     integer               (уникально в пределах рейса)
- boarding_time   timestamptz

Ограничения:
- UNIQUE (flight_id, boarding_no)
- UNIQUE (flight_id, seat_no)

FK → segments (ticket_no, flight_id)

## Таблица bookings.routes

- route_no           text        NOT NULL
- validity           tstzrange   NOT NULL
- departure_airport  char(3)     NOT NULL
- arrival_airport    char(3)     NOT NULL
- airplane_code      char(3)     NOT NULL
- days_of_week       integer[]   NOT NULL
- scheduled_time     time        NOT NULL
- duration           interval    NOT NULL

Ограничения:
- EXCLUDE USING gist (route_no WITH =, validity WITH &&)
- FK → airplanes_data.airplane_code
- FK → airports_data (departure_airport)
- FK → airports_data (arrival_airport)

Индекс: (departure_airport, lower(validity))

## Таблица bookings.flights

- flight_id           integer      PK
- route_no            text         NOT NULL
- status              text         NOT NULL
- scheduled_departure timestamptz  NOT NULL
- scheduled_arrival   timestamptz  NOT NULL
- actual_departure    timestamptz
- actual_arrival      timestamptz

Уникальность: (route_no, scheduled_departure)

CHECK:
- scheduled_arrival > scheduled_departure
- actual_arrival проверка логики
- status ∈ ('Scheduled','On Time','Delayed','Boarding','Departed','Arrived','Cancelled')

Ссылки на flights:
- segments.flight_id

## Таблица bookings.seats

- airplane_code    char(3)     PK (вместе с seat_no)
- seat_no          text        PK (вместе с airplane_code)
- fare_conditions  text        NOT NULL  (Economy / Comfort / Business)

FK → airplanes_data.airplane_code (ON DELETE CASCADE)

## Представление bookings.timetable

Объединяет flights + routes + airports_data (timezone)
Добавляет локальное время вылета/прилёта:

- flight_id
- route_no
- departure_airport
- arrival_airport
- status
- airplane_code
- scheduled_departure(_local)
- actual_departure(_local)
- scheduled_arrival(_local)
- actual_arrival(_local)

Полезно для простых запросов, но может быть неэффективно в сложных соединениях.

## Краткая сводка основных связей

- bookings → tickets (1:N)
- tickets → segments (1:N)
- flights → segments (1:N)
- segments → boarding_passes (1:N)
- routes → flights (1:N)   (по route_no + validity @> scheduled_departure)
- airplanes_data → routes (1:N)
- airplanes_data → seats (1:N)
- airports_data → routes (departure + arrival) (1:N)



Объекты схемы
Схема bookings содержит все объекты демонстрационной базы:

          Имя          |        Тип         |       Описание
-----------------------+--------------------+----------------------
 airplanes             | представление      | Самолёты
 airplanes_data        | таблица            | Самолёты (переводы)
 airports              | представление      | Аэропорты
 airports_data         | таблица            | Аэропорты (переводы)
 boarding_passes       | таблица            | Посадочные талоны
 bookings              | таблица            | Бронирования
 flights               | таблица            | Рейсы
 flights_flight_id_seq | последовательность |
 routes                | таблица            | Маршруты
 seats                 | таблица            | Места
 segments              | таблица            | Перелёты
 tickets               | таблица            | Билеты
 timetable             | представление      | Расписание
При подключении к базе параметр конфигурации search_path автоматически принимает значение bookings,"$user",public, так что явно указывать имя схемы необязательно.

Однако для функций bookings.now и bookings.version в любом случае необходимо явно указывать схему, чтобы отличать их от одноимённых стандартных функций.

Представление bookings.airplanes
Каждая модель воздушного судна идентифицируется трёхзначным кодом ИАТА (airplane_code). Указывается также название модели (model), максимальная дальность полета в километрах (range) и крейсерская скорость в километрах в час (speed).

Значение поля model определяется в зависимости от выбранного языка (параметр bookings.lang).

    Столбец    |   Тип   |              Описание
---------------+---------+------------------------------------
 airplane_code | char(3) |  Код самолёта, ИАТА
 model         | text    |  Модель самолёта
 range         | integer |  Максимальная дальность полета, км
 speed         | integer |  Крейсерская скорость, км/ч
Определение представления:
 SELECT airplane_code,
    model ->> lang() AS model,
    range,
    speed
   FROM airplanes_data ml;


Таблица bookings.airplanes_data
Это базовая таблица для представления airplanes. Поле model этой таблицы содержит переводы моделей самолётов на разные языки, в формате JSONB. В большинстве случаев к этой таблице не следует обращаться напрямую.

    Столбец    |   Тип   | Допустимость NULL |             Описание
---------------+---------+-------------------+-----------------------------------
 airplane_code | char(3) | not null          | Код самолёта, ИАТА
 model         | jsonb   | not null          | Модель самолёта
 range         | integer | not null          | Максимальная дальность полета, км
 speed         | integer | not null          | Крейсерская скорость, км/ч
Индексы:
    PRIMARY KEY, btree (airplane_code)
Ограничения-проверки:
    CHECK (range > 0)
    CHECK (speed > 0)
Ссылки извне:
    TABLE "routes" FOREIGN KEY (airplane_code)
        REFERENCES airplanes_data(airplane_code)
    TABLE "seats" FOREIGN KEY (airplane_code)
        REFERENCES airplanes_data(airplane_code) ON DELETE CASCADE


Представление bookings.airports
Аэропорт идентифицируется трёхбуквенным кодом ИАТА (airport_code) и имеет своё имя (airport_name).

Для города и страны не предусмотрено отдельных сущностей, но введены поля city и country, позволяющее найти аэропорты одного города или страны. Это представление также включает координаты аэропорта (coordinates) и часовой пояс (timezone).

Значения полей airport_name, city и country определяются в зависимости от выбранного языка (параметр bookings.lang).

   Столбец    |   Тип   |                  Описание
--------------+---------+------------------------------------------
 airport_code | char(3) |  Код аэропорта, ИАТА
 airport_name | text    |  Название аэропорта
 city         | text    |  Город
 country      | text    |  Страна
 coordinates  | point   |  Координаты аэропорта (долгота и широта)
 timezone     | text    |  Часовой пояс аэропорта
Определение представления:
 SELECT airport_code,
    airport_name ->> lang() AS airport_name,
    city ->> lang() AS city,
    country ->> lang() AS country,
    coordinates,
    timezone
   FROM airports_data ml;


Таблица bookings.airports_data
Это базовая таблица для представления airports. Она содержит переводы значений airport_name, city и country на разные языки, в формате JSONB. В большинстве случаев к этой таблице не следует обращаться напрямую.

   Столбец    |   Тип   | Допустимость NULL |                 Описание
--------------+---------+-------------------+-----------------------------------------
 airport_code | char(3) | not null          | Код аэропорта, ИАТА
 airport_name | jsonb   | not null          | Название аэропорта
 city         | jsonb   | not null          | Город
 country      | jsonb   | not null          | Страна
 coordinates  | point   | not null          | Координаты аэропорта (долгота и широта)
 timezone     | text    | not null          | Часовой пояс аэропорта
Индексы:
    PRIMARY KEY, btree (airport_code)
Ссылки извне:
    TABLE "routes" FOREIGN KEY (arrival_airport)
        REFERENCES airports_data(airport_code)
    TABLE "routes" FOREIGN KEY (departure_airport)
        REFERENCES airports_data(airport_code)


Таблица bookings.boarding_passes
При регистрации на первый рейс, которая возможна за сутки до плановой даты отправления, пассажиру выдаются посадочные талоны на все рейсы в билете. В посадочном талоне указывается номер места (seat_no). Посадочный талон идентифицируется также, как и перелёт — номером билета и идентификатором рейса.

При посадке пассажиров в самолёт посадочным талонам присваиваются последовательные номера (boarding_no, этот номер уникален только в пределах данного рейса) и фиксируется время посадки (boarding_time).

    Столбец    |     Тип     | Допустимость NULL |         Описание
---------------+-------------+-------------------+--------------------------
 ticket_no     | text        | not null          | Номер билета
 flight_id     | integer     | not null          | Идентификатор рейса
 seat_no       | text        | not null          | Номер места
 boarding_no   | integer     |                   | Номер посадочного талона
 boarding_time | timestamptz |                   | Время посадки
Индексы:
    PRIMARY KEY, btree (ticket_no, flight_id)
    UNIQUE CONSTRAINT, btree (flight_id, boarding_no)
    UNIQUE CONSTRAINT, btree (flight_id, seat_no)
Ограничения внешнего ключа:
    FOREIGN KEY (ticket_no, flight_id)
        REFERENCES segments(ticket_no, flight_id)


Таблица bookings.bookings
Продажа билетов начинается за 60 дней до рейса. Пассажир заранее (book_date) бронирует билет себе и, возможно, нескольким другим пассажирам. Бронирование идентифицируется шестизначной комбинацией букв и цифр (book_ref).

Поле total_amount хранит общую стоимость включённых в бронирование перелетов всех пассажиров.

   Столбец    |      Тип      | Модификаторы |         Описание
--------------+---------------+--------------+---------------------------
 book_ref     | char(6)       | not null     | Номер бронирования
 book_date    | timestamptz   | not null     | Дата бронирования
 total_amount | numeric(10,2) | not null     | Полная сумма бронирования
Индексы:
    PRIMARY KEY, btree (book_ref)
Ссылки извне:
    TABLE "tickets" FOREIGN KEY (book_ref) REFERENCES bookings(book_ref)


Таблица bookings.flights
Естественный ключ таблицы рейсов состоит из двух полей — номера маршрута (route_no) и плановой даты отправления (scheduled_departure). Чтобы сделать внешние ключи на эту таблицу компактнее, в качестве первичного используется суррогатный ключ (flight_id).

У каждого рейса есть запланированные дата и время вылета (scheduled_departure) и прибытия (scheduled_arrival). Реальные время вылета (actual_departure) и прибытия (actual_arrival) могут отличаться: обычно не сильно, но иногда и на несколько часов, если рейс задержан.

Статус рейса (status) может принимать одно из следующих значений:

Scheduled. Рейс доступен для бронирования. Это происходит за 60 дней до плановой даты вылета; до этого запись о рейсе не существует в базе данных.
On Time. Открыта регистрация (за сутки до плановой даты вылета) и рейс не задержан.
Delayed. Открыта регистрация (за сутки до плановой даты вылета), но рейс задержан.
Boarding. Идет посадка пассажиров в самолёт.
Departed. Самолёт вылетел и находится в воздухе.
Arrived. Самолёт прибыл в пункт назначения.
Cancelled. Рейс отменён.
       Столбец       |     Тип     | Допустимость NULL |          Описание
---------------------+-------------+-------------------+-----------------------------
 flight_id           | integer     | not null          | Идентификатор рейса
 route_no            | text        | not null          | Номер маршрута
 status              | text        | not null          | Статус рейса
 scheduled_departure | timestamptz | not null          | Время вылета по расписанию
 scheduled_arrival   | timestamptz | not null          | Время прилёта по расписанию
 actual_departure    | timestamptz |                   | Фактическое время вылета
 actual_arrival      | timestamptz |                   | Фактическое время прилёта
Индексы:
    PRIMARY KEY, btree (flight_id)
    UNIQUE CONSTRAINT, btree (route_no, scheduled_departure)
Ограничения-проверки:
    CHECK (scheduled_arrival > scheduled_departure)
    CHECK (actual_arrival IS NULL
       OR  ((actual_departure IS NOT NULL AND actual_arrival IS NOT NULL)
            AND (actual_arrival > actual_departure)))
    CHECK (status IN ( 'Scheduled', 'On Time', 'Delayed', 'Boarding',
                      'Departed', 'Arrived', 'Cancelled'))
Ссылки извне:
    TABLE "segments" FOREIGN KEY (flight_id)
        REFERENCES flights(flight_id)


Таблица bookings.routes
Маршрут всегда соединяет две точки — аэропорты вылета (departure_airport) и прибытия (arrival_airport). Такое понятие, как «маршрут с пересадками» отсутствует: если из одного аэропорта до другого нет прямого рейса, в билет просто включаются несколько перелетов.

Маршрут имеет период действия (validity) длиной в месяц. Маршрут между теми же аэропортами может повторяться неоднократно; он будет иметь тот же номер route_no, однако в разные периоды может обслуживаться разными самолётами и отправляться в разные дни.

Рейсы, следующие данным маршрутом, обслуживаются определенным типом самолёта (airplane_code) и вылетают в одно и то же время (scheduled_time, местное время в аэропорту отправления) в разные дни недели (массив days_of_week, 1 — понедельник, 7 — воскресенье).

       Столбец       |     Тип     | Допустимость NULL |          Описание
---------------------+-------------+-------------------+-----------------------------
 route_no            | text        | not null          | Номер маршрута
 validity            | tstzrange   | not null          | Период действия
 departure_airport   | char(3)     | not null          | Аэропорт отправления
 arrival_airport     | char(3)     | not null          | Аэропорт прибытия
 airplane_code       | char(3)     | not null          | Код самолёта, ИАТА
 days_of_week        | integer[]   | not null          | Дни недели, когда выполняются рейсы
 scheduled_time      | time        | not null          | Местное время вылета по расписанию
 duration            | interval    | not null          | Планируемая длительность полёта
Индексы:
    btree (departure_airport, lower(validity))
    EXCLUDE USING gist (route_no WITH =, validity WITH &&)
Ограничения внешнего ключа:
    FOREIGN KEY (airplane_code) REFERENCES airplanes_data(airplane_code)
    FOREIGN KEY (arrival_airport) REFERENCES airports_data(airport_code)
    FOREIGN KEY (departure_airport) REFERENCES airports_data(airport_code)


Таблица bookings.seats
Места определяют схему салона каждой модели. Каждое место определяется своим номером (seat_no) и имеет закреплённый за ним класс обслуживания (fare_conditions) — Economy, Comfort или Business.

     Столбец     |     Тип     | Допустимость NULL |      Описание
-----------------+-------------+-------------------+--------------------
 airplane_code   | char(3)     | not null          | Код самолёта, ИАТА
 seat_no         | text        | not null          | Номер места
 fare_conditions | text        | not null          | Класс обслуживания
Индексы:
    PRIMARY KEY, btree (airplane_code, seat_no)
Ограничения-проверки:
    CHECK (fare_conditions IN ('Economy', 'Comfort', 'Business'))
Ограничения внешнего ключа:
    FOREIGN KEY (airplane_code)
        REFERENCES airplanes_data(airplane_code) ON DELETE CASCADE


Таблица bookings.segments
Перелёт соединяет билет с рейсом и идентифицируется их номерами.

Для каждого перелета указываются его стоимость (price) и класс обслуживания (fare_conditions).

     Столбец     |     Тип       | Допустимость NULL |    Описание
-----------------+---------------+-------------------+---------------------
 ticket_no       | text          | not null          | Номер билета
 flight_id       | integer       | not null          | Идентификатор рейса
 fare_conditions | text          | not null          | Класс обслуживания
 price           | numeric(10,2) | not null          | Стоимость перелета
Индексы:
    PRIMARY KEY, btree (ticket_no, flight_id)
    btree (flight_id)
Ограничения-проверки:
    CHECK (price >= 0)
    CHECK (fare_conditions IN ('Economy', 'Comfort', 'Business'))
Ограничения внешнего ключа:
    FOREIGN KEY (flight_id) REFERENCES flights(flight_id)
    FOREIGN KEY (ticket_no) REFERENCES tickets(ticket_no)
Ссылки извне:
    TABLE "boarding_passes" FOREIGN KEY (ticket_no, flight_id)
        REFERENCES segments(ticket_no, flight_id)


Таблица bookings.tickets
Билет имеет уникальный номер (ticket_no), состоящий из 13 цифр.

Билет содержит информацию о пассажире: номер документа, удостоверяющего личность (passenger_id), а также его полное имя (passenger_name). Номер документа состоит из кода страны и цифрового идентификатора, а полное имя — из имени и фамилии (имя указывается первым даже для тех стран, в которых принят обратный порядок, как, например, в Китае).

Для пассажира нет отдельной сущности, но пассажир однозначно идентифицируется номером документа. Гарантируется, что одному номеру документа всегда соответствует одно и то же имя пассажира (в разных документах имена могут совпадать). Один и тот же пассажир не может участвовать в одном бронировании несколько раз и не может следовать разными рейсами в одно и то же время (хотя последнее условие не проверяется на уровне базы данных).

Признак прямого билета (outbound) имеет истинное значение для билета «туда» и ложное — для билета «обратно». Конечные пункты перелётов, включенных в прямой и обратный билеты, совпадают, но пути следования могут отличаться.

     Столбец    |     Тип     | Допустимость NULL |        Описание
----------------+-------------+-------------------+-------------------------
 ticket_no      | text        | not null          | Номер билета
 book_ref       | char(6)     | not null          | Номер бронирования
 passenger_id   | text        | not null          | Номер документа
 passenger_name | text        | not null          | Полное имя пассажира
 outbound       | boolean     | not null          | Является ли рейс прямым
Индексы:
    PRIMARY KEY, btree (ticket_no)
    UNIQUE CONSTRAINT, btree (book_ref, passenger_id, outbound)
Ограничения внешнего ключа:
    FOREIGN KEY (book_ref) REFERENCES bookings(book_ref)
Ссылки извне:
    TABLE "segments" FOREIGN KEY (ticket_no) REFERENCES tickets(ticket_no)


Представление bookings.timetable
Над таблицами routes и flights создано представление timetable, скрывающее темпоральное соединение и добавляющее информацию о местном времени вылета и прибытия. Представление позволяет упростить многие запросы, что особенно важно для тех, кто только начинает изучать язык SQL. Однако применение этого представления в сложных запросах может ухудшить производительность из-за потенциально лишних соединений с таблицами аэропортов.

          Столбец          |     Тип     |              Описание
---------------------------+-------------+--------------------------------------
 flight_id                 | integer     | Идентификатор рейса
 route_no                  | text        | Номер маршрута
 departure_airport         | char(3)     | Код аэропорта отправления
 arrival_airport           | char(3)     | Код аэропорта прибытия
 status                    | status      | Статус рейса
 airplane_code             | char(3)     | Код самолёта, ИАТА
 scheduled_departure       | timestamptz | Время вылета по расписанию
 scheduled_departure_local | timestamp   | Время вылета по расписанию,
                           |             | местное время в пункте отправления
 actual_departure          | timestamptz | Фактическое время вылета
 actual_departure_local    | timestamp   | Фактическое время вылета,
                           |             | местное время в пункте отправления
 scheduled_arrival         | timestamptz | Время прилёта по расписанию
 scheduled_arrival_local   | timestamp   | Время прилёта по расписанию,
                           |             | местное время в пункте прибытия
 actual_arrival            | timestamptz | Фактическое время прилёта
 actual_arrival_local      | timestamp   | Фактическое время прилёта,
                           |             | местное время в пункте прибытия
Определение представления:
 SELECT f.flight_id,
    f.route_no,
    r.departure_airport,
    r.arrival_airport,
    f.status,
    r.airplane_code,
    f.scheduled_departure,
    (f.scheduled_departure AT TIME ZONE dep.timezone) AS scheduled_departure_local,
    f.actual_departure,
    (f.actual_departure AT TIME ZONE dep.timezone) AS actual_departure_local,
    f.scheduled_arrival,
    (f.scheduled_arrival AT TIME ZONE arr.timezone) AS scheduled_arrival_local,
    f.actual_arrival,
    (f.actual_arrival AT TIME ZONE arr.timezone) AS actual_arrival_local
   FROM flights f
     JOIN routes r ON r.flight_no = f.flight_no AND r.validity @> f.scheduled_departure
     JOIN airports_data dep ON dep.airport_code = r.departure_airport
     JOIN airports_data arr ON arr.airport_code = r.arrival_airport;

Функция bookings.now
Демонстрационная база содержит временной «срез» данных — так, как будто в некоторый момент была сделана резервная копия реальной системы. Например, если некоторый рейс имеет статус Departed, это означает, что в момент резервного копирования самолёт вылетел и находился в воздухе.

Позиция «среза» сохранена в функции bookings.now. Ей можно пользоваться в запросах там, где в обычной жизни использовалась бы функция now.

Функция bookings.lang
Некоторые поля в демонстрационной базе содержат текст на английском и русском языках. Функция bookings.lang возвращает значение параметра bookings.lang, то есть язык, на котором будут выдаваться значения этих полей.

Эта функция используется в представлениях airplanes и airports и не предназначена для непосредственного использования в запросах.

Функция bookings.version
Функция bookings.version возвращает версию демонстрационной базы данных. Версия состоит из названия воображаемой авиакомпании и даты начала авиаперевозок, а также сообщает охваченный интервал времени. Актуальная версия на текущий момент — PostgresPro 2025-09-01.

Использование
По умолчанию значения различных переводимых полей выдаются на английском языке. Это поля airport_name, city и country представления airports, а также поле model представления airplanes.

Вы можете выбрать другой язык для отображения этих полей. Для переключения на русский (единственный перевод, представленный в данной базе) установите для параметра bookings.lang значение ru:

SET bookings.lang = 'ru';
Также может быть удобно выбрать язык на уровне базы данных:

ALTER DATABASE demo SET bookings.lang = 'ru';
Чтобы это изменение вступило в силу, необходимо повторно подключиться к базе данных.

Посмотрим на результаты нескольких простых запросов, чтобы лучше познакомиться с содержимым демонстрационной базы данных.

Результаты, представленные ниже, были получены для версии PostgresPro 2025-09-01 (91 days). Если в вашей системе запросы выдают другие данные, проверьте версию демонстрационной базы (функция bookings.version). Незначительные отклонения могут быть связаны с местным временем, отличным от московского, и настройками локализации.

Все рейсы выполняются несколькими типами самолётов:

SELECT * FROM airplanes;
 airplane_code |         model          | range | speed
---------------+------------------------+-------+-------
 32N           | Аэробус A320neo        |  6500 |   830
 339           | Аэробус A330-900neo    | 13300 |   870
 351           | Аэробус A350-1000      | 16700 |   913
 35X           | Аэробус A350F          |  8700 |   903
 76F           | Боинг 767-300F         |  6000 |   850
 77W           | Боинг 777-300ER        | 14600 |   905
 789           | Боинг 787-9 Dreamliner | 14000 |   913
 7M7           | Боинг 737 MAX 7        |  7000 |   840
 CR7           | Бомбардье CRJ700       |  3100 |   829
 E70           | Эмбраэр E170           |  4000 |   800
(10 строк)
Для каждого типа самолёта хранится список мест в салоне. Например, вот где можно разместиться в бизнес-классе Эмбраэра E170:

SELECT *
FROM seats
WHERE airplane_code = 'E70' AND fare_conditions = 'Business';
 airplane_code | seat_no | fare_conditions
---------------+---------+-----------------
 E70           | 1A      | Business
 E70           | 1C      | Business
 E70           | 1D      | Business
 E70           | 2A      | Business
 E70           | 2C      | Business
 E70           | 2D      | Business
(6 строк)
Самолёты большего размера имеют больше посадочных мест с разными классами обслуживания:

SELECT
    s.airplane_code,
    string_agg (s.fare_conditions || '(' || s.num || ')', ', ') AS fare_conditions
FROM (
        SELECT airplane_code, fare_conditions, count(*)::text AS num
        FROM seats
        GROUP BY airplane_code, fare_conditions
     ) s
GROUP BY s.airplane_code
ORDER BY s.airplane_code;
 airplane_code |             fare_conditions
---------------+-----------------------------------------
 32N           | Business(28), Economy(138)
 339           | Business(29), Economy(224), Comfort(28)
 351           | Economy(281), Business(44)
 77W           | Economy(326), Business(30), Comfort(48)
 789           | Economy(188), Business(48), Comfort(21)
 7M7           | Business(16), Economy(144)
 CR7           | Business(6), Economy(52), Comfort(12)
 E70           | Business(6), Economy(72)
(8 строк)
Два типа самолётов (Аэробус A350F и Боинг 767-300F) являются грузовыми и не участвуют в пассажирских авиаперевозках.

База данных содержит список практически всех относительно крупных аэропортов:

SELECT
    count(*) airports,
    count(distinct country||','||city) cities,
    count(distinct country) countries
FROM airports;
 airports | cities | countries
----------+--------+-----------
     5501 |   5157 |       230
(1 строка)
Например, к Москве относятся пять аэропортов:

SELECT airport_code, airport_name, coordinates, timezone
FROM airports
WHERE country = 'Россия' AND city = 'Москва';
 airport_code | airport_name |    coordinates    |   timezone
--------------+--------------+-------------------+---------------
 BKA          | Быково       | (38.06,55.6172)   | Europe/Moscow
 DME          | Домодедово   | (37.9063,55.4088) | Europe/Moscow
 OSF          | Остафьево    | (37.5072,55.5117) | Europe/Moscow
 SVO          | Шереметьево  | (37.4146,55.9726) | Europe/Moscow
 VKO          | Внуково      | (37.2615,55.5915) | Europe/Moscow
(5 rows)
Маршрутная сеть хранится в таблице routes. Вот, например, куда, в какие дни недели и за какое время можно долететь из Рима первого ноября 2025 года:

SELECT r.route_no, a.airport_code, a.airport_name, a.city, a.country, r.days_of_week, r.duration
FROM routes r
    JOIN airports a ON a.airport_code = r.arrival_airport
WHERE departure_airport = (SELECT airport_code FROM airports WHERE airport_name = 'Фьюмичино')
    AND validity @> '2025-11-01 00:00:00CET'::timestamptz;
 route_no | airport_code | airport_name |  city   |      country      |  days_of_week   | duration
----------+--------------+--------------+---------+-------------------+-----------------+----------
 PG0086   | BGY          | Бергамо      | Милан   | Италия            | {1,2,3,4,5,6,7} | 01:05:00
 PG0176   | ORY          | Орли         | Париж   | Франция           | {2,4,6,7}       | 01:55:00
 PG0228   | HGH          | Сяошань      | Ханчжоу | Китай             | {7}             | 11:30:00
 PG0233   | MXP          | Мальпенса    | Милан   | Италия            | {1,2,3,4,5,6,7} | 01:05:00
 PG0235   | ORD          | О'Хара       | Чикаго  | Соединенные Штаты | {2}             | 09:50:00
(5 строк)
Обратите внимание, что время указано в часовом поясе аэропорта вылета (CET, Central European Time).

База данных была сформирована на момент, возвращаемый функцией bookings.now:

SELECT bookings.now();
          now
------------------------
 2025-12-01 00:00:00+03
(1 строка)
Относительно именно этого момента все рейсы делятся на прошедшие и будущие.

SELECT
    status,
    count(*) AS count,
    min(scheduled_departure) AS min_scheduled_departure,
    max(scheduled_departure) AS max_scheduled_departure
FROM flights
GROUP BY status
ORDER BY min_scheduled_departure;
  status   | count | min_scheduled_departure | max_scheduled_departure
-----------+-------+-------------------------+-------------------------
 Arrived   | 10966 | 2025-10-01 03:00:00+03  | 2025-12-01 02:10:00+03
 Cancelled |   121 | 2025-10-01 15:25:00+03  | 2026-01-29 19:20:00+03
 Departed  |    20 | 2025-11-30 15:50:00+03  | 2025-12-01 02:50:00+03
 Boarding  |     4 | 2025-12-01 02:55:00+03  | 2025-12-01 03:25:00+03
 Delayed   |    10 | 2025-12-01 03:30:00+03  | 2025-12-02 01:00:00+03
 On Time   |   157 | 2025-12-01 03:35:00+03  | 2025-12-02 02:55:00+03
 Scheduled | 10480 | 2025-12-02 03:10:00+03  | 2026-01-30 02:55:00+03
(7 строк)
Найдем ближайший рейс, вылетающий из Екатеринбурга (аэропорт SVX) в Ухань (аэропорт WUH). Воспользуемся представлением timetable, чтобы не соединять таблицы routes и flights:

SELECT *
FROM timetable t
WHERE t.departure_airport = 'SVX'
  AND t.arrival_airport = 'WUH'
  AND t.scheduled_departure > bookings.now()
ORDER BY t.scheduled_departure
LIMIT 1 \gx
-[ RECORD 1 ]-------------+-----------------------
flight_id                 | 11465
route_no                  | PG0522
departure_airport         | SVX
arrival_airport           | WUH
status                    | Scheduled
airplane_code             | 7M7
scheduled_departure       | 2025-12-03 10:30:00+03
scheduled_departure_local | 2025-12-03 12:30:00
actual_departure          |
actual_departure_local    |
scheduled_arrival         | 2025-12-03 17:30:00+03
scheduled_arrival_local   | 2025-12-03 22:30:00
actual_arrival            |
actual_arrival_local      |
Обратите внимание, что в представлении timetable указано не только локальное (московское) время, но и местное время в аэропортах вылета и прилёта.

Каждое бронирование может включать несколько билетов, по одному на каждого пассажира. Билет, в свою очередь, может включать несколько перелётов. Полная информация о бронировании находится в трёх таблицах: bookings, tickets и segments.

Посмотрим на бронирование с кодом JU35I4:

SELECT * FROM bookings WHERE book_ref = 'JU35I4';
 book_ref |           book_date           | total_amount
----------+-------------------------------+--------------
 JU35I4   | 2025-10-09 06:53:16.710703+03 |     86750.00
(1 строка)
Вот из каких билетов оно состоит:

SELECT *
FROM tickets
WHERE book_ref = 'JU35I4';
   ticket_no   | book_ref |   passenger_id   |  passenger_name   | outbound
---------------+----------+------------------+-------------------+----------
 0005433348362 | JU35I4   | RU 2714075620824 | Nadezhda Sergeeva | t
 0005433348356 | JU35I4   | RU 8692103212506 | Artur Isakov      | t
(2 строки)
Как мы видим, в бронирование входят билеты двух пассажиров. Узнаем, какие перелёты включены в билет Надежды Сергеевой:

SELECT r.route_no,
    dep.airport_code dep_airport, dep.country dep_country, dep.city dep_city,
    arr.airport_code arr_airport, arr.country arr_country, arr.city arr_city
FROM segments s
    JOIN flights f ON f.flight_id = s.flight_id
    JOIN routes r ON r.route_no = f.route_no AND r.validity @> f.scheduled_departure
    JOIN airports dep ON dep.airport_code = r.departure_airport
    JOIN airports arr ON arr.airport_code = r.arrival_airport
WHERE s.ticket_no = '0005433348362'
ORDER BY f.scheduled_departure;
 route_no | dep_airport | dep_country |      dep_city      | arr_airport | arr_country |      arr_city
----------+-------------+-------------+--------------------+-------------+-------------+--------------------
 PG0370   | OVB         | Россия      | Новосибирск        | SVO         | Россия      | Москва
 PG0179   | SVO         | Россия      | Москва             | FRA         | Германия    | Франкфурт-на-Майне
 PG0408   | FRA         | Германия    | Франкфурт-на-Майне | FCO         | Италия      | Рим
 PG0482   | FCO         | Италия      | Рим                | HEL         | Финляндия   | Хельсинки
(3 строки)
Как видим, Наталья летит из Новосибирска в Хельсинки с пересадками в Москвве, Франкфурте-на-Майне и Риме.

Часть перелётов в этом билете уже выполнены на момент, возвращаемый функцией bookings.now, а часть — ещё нет. После регистрации на первый рейс пассажиру выдаются посадочные талоны с указанием мест. В первых двух посадочных талонах Надежды указаны номер и время посадки в самолёт, а на следующие два рейса посадка ещё предстоит:

SELECT f.route_no, f.flight_id, f.status, bp.seat_no, bp.boarding_no, bp.boarding_time
FROM flights f
    JOIN boarding_passes bp ON bp.flight_id = f.flight_id
WHERE bp.ticket_no = '0005433348362'
ORDER BY f.scheduled_departure;
 route_no | flight_id |  status   | seat_no | boarding_no |         boarding_time
----------+-----------+-----------+---------+-------------+-------------------------------
 PG0370   |     10817 | Arrived   | 17B     |          45 | 2025-11-29 18:18:42.972147+03
 PG0179   |     10935 | Arrived   | 16A     |          33 | 2025-11-30 11:54:41.297034+03
 PG0408   |     11108 | On Time   | 24C     |             |
 PG0482   |     11264 | Scheduled | 4B      |             |
(4 строки)
Надеемся, что эти несколько простых примеров помогли составить представление о содержимом демонстрационной базы данных.

# Демонстрационная база данных bookings — временной срез и специальные функции

## Функция bookings.now
Функция `bookings.now()` возвращает момент времени, на который сделан «срез» демонстрационной базы данных.

Это аналог обычной функции `now()`, но фиксированный для всей базы.

Текущее значение (версия PostgresPro 2025-09-01):
2025-12-01 00:00:00+03 (московское время)

Все статусы рейсов (`Departed`, `Arrived`, `Boarding`, `On Time`, `Scheduled`, `Delayed`, `Cancelled`) интерпретируются относительно именно этого момента.

Использование в запросах:
- вместо `now()` → `bookings.now()`
- фильтрация будущих рейсов: `scheduled_departure > bookings.now()`
- определение, выполнен ли рейс: `scheduled_departure < bookings.now()`

## Функция bookings.lang
Функция `bookings.lang()` возвращает текущий код языка для отображения переводимых полей.

Поддерживаемые значения в этой версии базы:
- 'en' — английский (по умолчанию)
- 'ru' — русский

Переводятся поля в представлениях:
- airplanes.model
- airports.airport_name
- airports.city
- airports.country

Как переключить на русский:
SET bookings.lang = 'ru';

Или на уровне базы (требует переподключения):
ALTER DATABASE demo SET bookings.lang = 'ru';

Функция используется внутри определений представлений airplanes и airports — напрямую в запросах её обычно не пишут.

## Функция bookings.version
Функция `bookings.version()` возвращает строку с информацией о версии демонстрационной базы.

Пример вывода (актуально на 2025–2026):
PostgresPro 2025-09-01 (91 days)

Содержит:
- название воображаемой авиакомпании
- дата начала авиаперевозок в срезе
- длительность охваченного периода

Рекомендуется проверять при расхождении результатов запросов между разными копиями базы.

## Ключевые примеры и особенности данных (версия PostgresPro 2025-09-01)

### Самолёты (представление airplanes)
10 типов самолётов, из них 2 грузовых (A350F, 767-300F) — в пассажирских рейсах не участвуют.

Примеры кодов:
- 32N  → Аэробус A320neo
- 789  → Боинг 787-9 Dreamliner
- E70  → Эмбраэр E170
- 7M7  → Боинг 737 MAX 7

### Места (таблица seats)
Классы обслуживания: Economy, Comfort, Business.

Пример бизнес-класса E70:
- 1A, 1C, 1D, 2A, 2C, 2D (всего 6 мест)

Распределение по моделям (пример агрегации):
- 77W → Economy(326), Business(30), Comfort(48)
- 351 → Economy(281), Business(44)
- CR7 → Business(6), Economy(52), Comfort(12)

### Аэропорты (представление airports)
- Всего аэропортов: 5501
- Уникальных городов: 5157
- Стран: 230

Пример — Москва (5 аэропортов):
- SVO → Шереметьево
- DME → Домодедово
- VKO → Внуково
- BKA → Быково
- OSF → Остафьево

### Рейсы и статусы (таблица flights)
Распределение статусов на момент 2025-12-01 00:00:00+03:
- Arrived    — 10 966
- Scheduled  — 10 480
- Cancelled  — 121
- Departed   — 20
- Boarding   — 4
- Delayed    — 10
- On Time    — 157

Будущие рейсы начинаются примерно с 2025-12-02.

### Пример ближайшего рейса (SVX → WUH)
Используя представление timetable:
- flight_id     11465
- route_no      PG0522
- airplane      7M7 (737 MAX 7)
- вылет         2025-12-03 10:30:00+03 (локально 12:30)
- прилёт        2025-12-03 17:30:00+03 (локально 22:30)

### Пример бронирования JU35I4
- Дата брони: 2025-10-09
- Сумма: 86 750 руб
- 2 пассажира:
  - Nadezhda Sergeeva (туда)
  - Artur Isakov      (туда)

Перелёты Надежды Сергеевой:
1. OVB → SVO (PG0370) — уже Arrived, место 17B
2. SVO → FRA (PG0179) — уже Arrived, место 16A
3. FRA → FCO (PG0408) — On Time, место 24C
4. FCO → HEL (PG0482) — Scheduled, место 4B

## Рекомендации по использованию в запросах
- Всегда используйте `bookings.now()` вместо `now()` для воспроизводимости
- Проверяйте `bookings.version()` при неожиданных результатах
- Для русскоязычных названий устанавливайте `SET bookings.lang = 'ru';`
- Представление `timetable` удобно для простых запросов по расписанию с местным временем
