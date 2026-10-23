# Open Skies — сборка NeoForge 1.21.1 Артёма и друзей

Своя сборка «Open Skies» в [packwiz](https://packwiz.infra.link/): Create, Create Aeronautics, Incoming, дальняя
прорисовка Voxy (через Roxy), шейдеры, запись повторов, на сервере — Almighty. Что в ней и как её ставить — README.md. Мод — https://github.com/zentixua/incoming,
мост ведущего Almighty (только сервер) — https://github.com/zentixua/almighty.

## Люди и правила
- Автор/хост: **Артём** (GitHub zentixua, в игре ZentixUA). Друзья: **ENOTzRPG**, **WallyFillmark**. Общаемся
  по-русски, кратко и по делу.
- **`pack/` на `main` — живая сборка**: экземпляры игроков с автообновлением (Prism, packwiz-installer перед каждым
  запуском) и выделенный сервер ставят её с `main` при следующем запуске. В `main` — только проверенное CI и только jar
  из уже вышедших выпусков (PR сборки — после выпуска мода).
- Сборка чистая и надёжная: стандартные механизмы, без обходов; настройки чужих модов — по умолчанию, а каждый файл
  в `config/` — с причиной в README.md. Новый обязательный мод — только по слову Артёма.
- Версию (`version` в `pack.toml`) поднимать при каждом изменении состава и строку в таблицу версий README.md:
  у всех игроков один набор.
- Выпуск на GitHub — сам: новая `version` на `main` выходит релизом `v<version>` (скачивание без входа по
  `releases/latest/download/Open-Skies.zip` и `…/Open-Skies.mrpack`).
  Остальные публичные шаги (Modrinth и др.) — только по прямому слову Артёма.
- Готовый PR вливать самому после зелёного CI, чистого независимого ревью и вердикта координатора.

## Где что лежит
```
pack/                    ← сама сборка: pack.toml (версии игры и NeoForge), index.toml, mods/*.pw.toml и
                           shaderpacks/*.pw.toml (откуда скачать и хеш), config/ (кладётся в игру как есть)
tools/prism_instance.py  ← экземпляр Prism, который ставит pack/ с main сам при каждом запуске (Open-Skies.zip)
tools/pack_dir.py        ← каталог игры из pack/ без Prism (моды по хешам) — для проверок клиентом Incoming
tools/check_loader.py    ← каждый мод (и вложенные jar) принимает NeoForge из pack.toml; шаг CI
tools/boot_check.py      ← сборка с нуля запускается: сервер до «Done», клиент до входа в мир; задача CI «Запуск
                           с нуля» (клиент — Xvfb и Mesa), руками — клиент во вложенном KWin Incoming (шапка скрипта)
.github/workflows/build.yml  ← CI «Сборка модов»: индекс свежий, .mrpack и экземпляр Prism (артефакт open-skies);
                               и «Запуск с нуля» (boot_check.py); новая version на main — релиз v<version> с ними,
                               только если обе прошли (заметки — строка README «Версии»)
```
Адрес сборки для packwiz-installer: `https://raw.githubusercontent.com/zentixua/open-skies/main/pack/pack.toml`;
экземпляры, поставленные под прежним именем сборки (Airstrike Pack), берут её по старому адресу
`zentixua/airstrike-pack/…` — GitHub отдаёт его, пока у zentixua нет репозитория с этим именем (имя не занимать).
Сборка лежит в `pack/`, а не в корне: файлы репозитория (README, CI, инструменты) не попадают в индекс и в игру.

## Рабочий цикл
```sh
go install github.com/packwiz/packwiz@v0.0.0-20260906154125-ef87d964f8cb
cd pack && packwiz update <имя>           # мод с Modrinth; точная версия — packwiz modrinth add --project-id … --version-id …
cd pack && packwiz refresh                # индекс с хешами — тем же коммитом (CI проверяет)
cd pack && packwiz mr export              # .mrpack — разовая установка без автообновления
python3 tools/prism_instance.py           # dist/Open-Skies.zip — новый экземпляр с автообновлением
```
Новый выпуск Incoming: `packwiz url add Incoming https://github.com/zentixua/incoming/releases/download/v<версия>/incoming-<версия>.jar --meta-name incoming`;
Almighty — так же, `almighty-<версия>.jar` из выпуска https://github.com/zentixua/almighty, `side = "server"`.

## Подводные камни
- `config/fml.toml` сборки держит `maxThreads = 1`: NeoForge создаёт моды параллельно, а Create 6.0.10 регистрирует
  предметы через таблицы не для нескольких потоков — изредка запуск падает с `Trying to access unbound value …
  create:…` (README, «Настройки»). Убирать — только когда Create это исправит.
- Roxy грузит только `voxy-0.2.16-beta+1.21.11` (Modrinth `H3w2nVdU`): Voxy не обновлять, пока Roxy не скажет
  про другую версию. Roxy и Voxy — необязательные с галочкой по умолчанию, включаются и выключаются только вместе.
- GitHub отдаёт raw-файлы с кэшем до 5 минут: сразу после слияния `pack.toml` и `index.toml` могут быть из разных
  коммитов — packwiz-installer скажет про неверный хеш индекса («Quit», запустить позже). Сервер перезапускать через
  ~5 минут после слияния.
- `side` у модов должен быть верным: сервер ставит сборку с `-s server`, `client` он не ставит; мод только для сервера
  (Almighty) — `side = "server"`, игрокам он не скачивается.
- packwiz-installer удаляет только то, что ставил сам: экземпляр из `.mrpack` переводят на автообновление, убрав
  `mods` в сторону (README.md), иначе старый jar с другим именем остался бы рядом с новым.
- Путь в индексе не выходит за `pack/` (packwiz-installer отбрасывает лишние `..`), а `pack.toml` несёт хеш индекса:
  сборку нельзя перенаправить на другой адрес содержимым файлов — новый адрес вписывается в «Предстартовую команду»
  экземпляра. Переименование репозитория GitHub адрес не ломает: raw.githubusercontent.com отдаёт файлы и по старому
  имени.
- Экземпляр с другим адресом в «Предстартовой команде» сборку с `main` не получает — его ставят заново из
  `Open-Skies.zip`.
