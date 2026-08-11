Это Kotlin Multiplatform шаблонный проект с таргетами Android, iOS, Web, Desktop (JVM).

* [/iosApp](./iosApp/iosApp) — iOS-приложение. Даже если UI шарится через Compose Multiplatform,
  эта точка входа всё равно нужна для iOS-приложения. Сюда же добавляется SwiftUI-код, если он понадобится.

* [/shared](./shared/src) — код, общий для всех Compose Multiplatform приложений.
  Содержит несколько подпапок:
  - [commonMain](./shared/src/commonMain/kotlin) — код, общий для всех таргетов.
  - Остальные папки — код, который компилируется только под платформу, указанную в названии папки.
    Например, если нужно использовать Apple CoreCrypto в iOS-части — [iosMain](./shared/src/iosMain/kotlin)
    подходящее место для такого кода. Аналогично для Desktop (JVM)-специфичного кода — папка
    [jvmMain](./shared/src/jvmMain/kotlin).

### Базовая конфигурация

| | |
|---|---|
| Gradle | 9.7.0 |
| Kotlin | 2.4.10 |
| AGP (Android Gradle Plugin) | 9.2.1 |
| Compose Multiplatform | 1.11.1 |
| Android compileSdk / targetSdk | 37 |
| Android minSdk | 28 |
| JVM target | 11 |
| ktlint (плагин) | 14.2.0 |
| detekt (плагин) | 1.23.8 |
| Koin | 4.2.2 |
| Navigation3 | 1.1.1 |
| Compottie | 2.2.4 |

Версии зафиксированы централизованно в [gradle/libs.versions.toml](./gradle/libs.versions.toml)
(version catalog) — там же и остальные зависимости (AndroidX, kotlinx.coroutines и т.д.).

### Что уже настроено

Шаблон идёт с небольшим готовым базисом, чтобы не собирать его заново в каждом новом проекте:

- **DI** — [Koin](https://insert-koin.io/), разложен по слоям `di/{App,Data,Domain,ViewModels}Module`
  (папка `di/` внутри [shared-модуля](./shared/src/commonMain/kotlin), пакет `com.shashluchok.<ваш-пакет>`).
  Платформенные модули (например, Android) передаются в общую composable `AppContent()`
  через параметр `platformModule`.
- **Навигация + экраны** — [Navigation3](https://developer.android.com/guide/navigation/navigation-3),
  с минимальным MVI-скелетом экрана (`BaseViewModel`, `*State`, `*Action`) в
  `presentation/screen` внутри [shared-модуля](./shared/src/commonMain/kotlin).
- **Тема** — `AppTheme`/`Dimens`/цветовая схема в
  `presentation/theme` внутри [shared-модуля](./shared/src/commonMain/kotlin).
  Цвета сейчас заглушки (`Color.Unspecified`) — замените на реальные дизайн-токены под конкретный проект.
- **Конвенция строковых ключей** — формат `[dev__](screen_X|dialog_X)__component[__type][__property]`,
  проверяется через [config/string-keys](./config/string-keys) (подробнее — ниже, в разделе про git-хуки).
- **Git-хуки** — ktlint, detekt и проверка формата строковых ключей на застейдженных файлах при коммите
  (подробнее — ниже).
- **Lottie-анимации** — [Compottie](https://github.com/alexzhirkevich/compottie), рендерер Lottie
  на чистом Kotlin (без platform delegates), работает на всех таргетах шаблона, включая
  Wasm/JS. Подключены `compottie` и `compottie-resources` — второй модуль умеет грузить
  анимации прямо из compose-ресурсов (`LottieCompositionSpec.Resource(...)`).

### Git-хуки

`.githooks/pre-commit` гоняется при каждом `git commit` и проверяет только застейдженные файлы:

- **Формат ключей строковых ресурсов.** Если среди застейдженных файлов есть `strings.xml`
  (Android / Compose Multiplatform resources) или `.strings` (iOS), их ключи прогоняются через
  [config/string-keys/validate_string_keys.py](./config/string-keys/validate_string_keys.py) на
  соответствие формату `[dev__](screen_X|dialog_X)__component[__type][__property]` (сама конвенция
  и когда нужны `__type`/`__property` — в скилле `string-resource-keys`). Проверка механическая
  (регистр, разделители, форма), не семантическая — коммит с кривым ключом просто не пройдёт.
  - **Allowlist** — [config/string-keys/allowlist.txt](./config/string-keys/allowlist.txt): ключи,
    которые не подчиняются конвенции и не должны считаться нарушением (например, `app_name` —
    имя, навязанное платформой, а не фичей). Одна запись на строку, `#` — комментарии.
- **ktlint + detekt.** Если среди застейдженных файлов есть `.kt`/`.kts`, оба гоняются, но только по
  застейдженным файлам, а не по всему проекту — быстрее и не блокирует коммит из-за несвязанных
  файлов, которые вы не трогали.

- detekt-правило `CompositionLocalAllowlist` и ktlint-правило `compose_allowed_composition_locals`
ругаются на любой `CompositionLocal`, которого нет в белом списке (сейчас там только
`LocalDimens`). При добавлении нового — впишите его в оба места:
[config/detekt/detekt.yml](./config/detekt/detekt.yml) (`CompositionLocalAllowlist.allowedCompositionLocals`)
и [.editorconfig](./.editorconfig) (`compose_allowed_composition_locals`).

Хук подключается автоматически: при первом запуске Gradle (`./gradlew ...`) корневой
`build.gradle.kts` сам выставляет `core.hooksPath=.githooks` в локальном `.git/config` — руками
`git config` делать не нужно.

### Настройка под новый проект

> Весь этот раздел и папка [/bootstrap](./bootstrap) нужны только один раз, при создании нового
> проекта из шаблона. После шага 5 можно удалить и папку `bootstrap/`, и сам этот раздел из README —
> в реальном проекте они больше не пригодятся.

1. Нажмите "Use this template" → "Create a new repository" на странице
   [TemplateKmpProject на GitHub](https://github.com/shashluchok/TemplateKmpProject) и создайте
   новый репозиторий в своём аккаунте. GitHub сам создаст его с чистой историей (без связи
   с шаблоном как fork).
2. Склонируйте уже свой новый репозиторий.
3. Отредактируйте [bootstrap/template.toml](./bootstrap/template.toml) — `app_name`
   (отображаемое имя) и `package` .
4. Один раз запустите `python bootstrap/bootstrap_project.py`. Переименует и пакет
   (включая директории — вложенность может быть любой), и саму папку проекта на диске
   в `app_name`. Это просто подстановка текста, импорты не переупорядочивает — если
   новый пакет сильно отличается по алфавитному порядку от старого, ktlint может
   пожаловаться на порядок импортов в паре файлов; правится одним `./gradlew ktlintFormat`.
   - Переименование самой папки на диске может не выполниться, останется только закрыть всё, что открыто на этой папке,
     и переименовать её вручную.
5. Удалите папку `bootstrap/` — она больше не нужна.

### Запуск приложений

Используйте конфигурации запуска из тулбара IDE. Либо эти команды:

- Android-приложение: `./gradlew :androidApp:assembleDebug`
- Desktop-приложение:
  - С hot reload: `./gradlew :desktopApp:hotRun --auto`
  - Обычный запуск: `./gradlew :desktopApp:run`
- Web-приложение:
  - Wasm-таргет (быстрее, современные браузеры): `./gradlew :webApp:wasmJsBrowserDevelopmentRun`
  - JS-таргет (медленнее, поддерживает старые браузеры): `./gradlew :webApp:jsBrowserDevelopmentRun`
- iOS-приложение: открыть директорию [/iosApp](./iosApp) в Xcode и запустить оттуда.

### Запуск тестов

Через кнопку запуска в IDE, либо Gradle-таски:

- Android-тесты: `./gradlew :shared:testAndroidHostTest`
- Desktop-тесты: `./gradlew :shared:jvmTest`
- Web-тесты:
  - Wasm-таргет: `./gradlew :shared:wasmJsTest`
  - JS-таргет: `./gradlew :shared:jsTest`
- iOS-тесты: `./gradlew :shared:iosSimulatorArm64Test`

---
