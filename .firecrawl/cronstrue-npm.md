skip to: [content](https://www.npmjs.com/package/cronstrue#main) [package search](https://www.npmjs.com/package/cronstrue#search) [sign in](https://www.npmjs.com/package/cronstrue#signin)

❤

- [Pro](https://www.npmjs.com/products/pro)
- [Teams](https://www.npmjs.com/products/teams)
- [Pricing](https://www.npmjs.com/products)
- [Documentation](https://docs.npmjs.com/)

npm

[Npm](https://www.npmjs.com/)

Search

[Sign Up](https://www.npmjs.com/signup) [Sign In](https://www.npmjs.com/login)

# cronstrue  ![TypeScript icon, indicating that this package has built-in type declarations](https://static-production.npmjs.com/4a2a680dfcadf231172b78b1d3beb975.svg)

3.14.0 • Public • Published 15 days ago

- [Readme](https://www.npmjs.com/package/cronstrue?activeTab=readme)
- [Code Beta](https://www.npmjs.com/package/cronstrue?activeTab=code)
- [0 Dependencies](https://www.npmjs.com/package/cronstrue?activeTab=dependencies)
- [370 Dependents](https://www.npmjs.com/package/cronstrue?activeTab=dependents)
- [214 Versions](https://www.npmjs.com/package/cronstrue?activeTab=versions)

# cRonstrue ![Build Status](https://github.com/bradymholt/cRonstrue/workflows/Build/badge.svg)[![NPM Package](https://img.shields.io/npm/v/cronstrue.svg)](https://www.npmjs.com/package/cronstrue)

[Permalink: cRonstrue ](https://www.npmjs.com/package/cronstrue#cronstrue--)

![](https://user-images.githubusercontent.com/759811/210273710-b13913e2-0a71-4d9d-94da-1fe538b8a73e.gif)

**Would you take a quick second and ⭐️ my repo?**

cRonstrue is a JavaScript library that parses a cron expression and outputs a human readable description of the cron schedule. For example, given the expression "\*/5 \* \* \* \*" it will output "Every 5 minutes".

This library was ported from the original C# implementation called [cron-expression-descriptor](https://github.com/bradymholt/cron-expression-descriptor) and is also available in a [few other languages](https://github.com/bradymholt/cron-expression-descriptor#ports).

## Features

[Permalink: Features](https://www.npmjs.com/package/cronstrue#features)

- Zero dependencies
- Supports all cron expression special characters including \* / , - ? L W, #
- Supports 5, 6 (w/ seconds or year), or 7 (w/ seconds and year) part cron expressions
- [Quartz Job Scheduler](http://www.quartz-scheduler.org/) cron expressions are supported
- Supports time specification _nicknames_ (@yearly, @annually, @monthly, @weekly, @daily)
- i18n support with 30+ languages

## Demo

[Permalink: Demo](https://www.npmjs.com/package/cronstrue#demo)

A demo is available [here](http://bradymholt.github.io/cRonstrue/#cronstrue-demo).

## Installation

[Permalink: Installation](https://www.npmjs.com/package/cronstrue#installation)

cRonstrue is exported as an [UMD](https://github.com/umdjs/umd) module so it will work in an [AMD](https://github.com/amdjs/amdjs-api/wiki/AMD), [CommonJS](http://wiki.commonjs.org/wiki/CommonJS) or browser global context.

First, install the module:

```
npm install cronstrue
```

Then, depending upon your usage context, add a reference to it:

### Node / CommonJS

[Permalink: Node / CommonJS](https://www.npmjs.com/package/cronstrue#node--commonjs)

```
const cronstrue = require('cronstrue');
```

### ESM / webpack / TypeScript

[Permalink: ESM / webpack / TypeScript](https://www.npmjs.com/package/cronstrue#esm--webpack--typescript)

```
import cronstrue from 'cronstrue';
```

### Browser

[Permalink: Browser](https://www.npmjs.com/package/cronstrue#browser)

The `cronstrue.min.js` file from the `/dist` folder in the npm package should be served to the browser. There are no dependencies so you can simply include the library in a `<script>` tag.

```
<script src="cronstrue.min.js" type="text/javascript"></script>
<script>
  var cronstrue = window.cronstrue;
</script>
```

#### CDN

[Permalink: CDN](https://www.npmjs.com/package/cronstrue#cdn)

A simple way to load the library in a browser is by using the [unpkg](https://unpkg.com/) CDN, which is a
"fast, global content delivery network for everything on npm". To use it, include a script tag like this in your file:

```
<script src="https://unpkg.com/cronstrue@latest/dist/cronstrue.min.js" async></script>
```

Using the "latest" tag will result in a 302 redirect to the latest version tag so it is recommended to use a specific version tag such as [https://unpkg.com/cronstrue@1.48.0/dist/cronstrue.min.js](https://unpkg.com/cronstrue@1.48.0/dist/cronstrue.min.js) to avoid this redirect.

## Usage

[Permalink: Usage](https://www.npmjs.com/package/cronstrue#usage)

```
cronstrue.toString("* * * * *");
> "Every minute"

cronstrue.toString("0 23 ? * MON-FRI");
> "At 11:00 PM, Monday through Friday"

cronstrue.toString("0 23 * * *", { verbose: true });
> "At 11:00 PM, every day"

cronstrue.toString("23 12 * * SUN#2");
> "At 12:23 PM, on the second Sunday of the month"

cronstrue.toString("23 14 * * SUN#2", { use24HourTimeFormat: true });
> "At 14:23, on the second Sunday of the month"

cronstrue.toString("* * * ? * 2-6/2", { dayOfWeekStartIndexZero: false });
> "Every second, every 2 days of the week, Monday through Friday"

cronstrue.toString("* * * 6-8 *", { monthStartIndexZero: true });
> "Every minute, July through September"

cronstrue.toString("@monthly");
> "At 12:00 AM, on day 1 of the month"
```

For more usage examples, including a demonstration of how cRonstrue can handle some very complex cron expressions, you can [reference the unit tests](https://github.com/bradymholt/cRonstrue/blob/main/test/cronstrue.ts).

### i18n

[Permalink: i18n](https://www.npmjs.com/package/cronstrue#i18n)

By default, only the English translation (`en`) is included when you import and use cRonstrue. To use other languages, please see the [i18n section](https://www.npmjs.com/package/cronstrue#i18n-1) below.

### CLI Usage

[Permalink: CLI Usage](https://www.npmjs.com/package/cronstrue#cli-usage)

```
$ npm install -g cronstrue

$ cronstrue 1 2 3 4 5
At 02:01 AM, on day 3 of the month, and on Friday, only in April

$ cronstrue 1 2 3
Error: too few arguments (3): 1 2 3
Usage (5 args): cronstrue minute hour day-of-month month day-of-week
or
Usage (6 args): cronstrue second minute hour day-of-month month day-of-week
or
Usage (7 args): cronstrue second minute hour day-of-month month day-of-week year
```

## Options

[Permalink: Options](https://www.npmjs.com/package/cronstrue#options)

An options object can be passed as the second parameter to `cronstrue.toString`. The following options are available:

- **throwExceptionOnParseError: boolean** \- If exception occurs when trying to parse expression and generate description, whether to throw or catch and output the Exception message as the description. (Default: true)
- **verbose: boolean** \- Whether to use a verbose description (Default: false)
- **dayOfWeekStartIndexZero: boolean** \- Whether to interpret cron expression DOW `1` as Sunday or Monday. (Default: true)
- **monthStartIndexZero: boolean** \- Whether to interpret January as `0` or `1`. (Default: false)
- **use24HourTimeFormat: boolean** \- If true, descriptions will use a [24-hour clock](https://en.wikipedia.org/wiki/24-hour_clock) (Default: false but some translations will default to true)
- **trimHoursLeadingZero: boolean** \- Whether to trim the leading zero that may appear in the hours description; e.g. "02:00 AM" -> "2:00 AM", "08:00" -> "8:00" (Default: false)
- **locale: string** \- The locale to use (Default: "en")
- **logicalAndDayFields: boolean** \- If true, descriptions for cron expressions with both day of month and day of week specified will follow a logical-AND wording rather than logical-OR wording; e.g. "...between day 11 and 17 of the month, only on Friday" rather than "...between day 11 and 17 of the month, and on Friday" (Default: false)

## i18n

[Permalink: i18n](https://www.npmjs.com/package/cronstrue#i18n-1)

To use the i18n support cRonstrue provides, you can either import all the supported locales at once (using `cronstrue/i18n`) or import individual locales (using `cronstrue/locales/[locale]`). Then, when calling `toString` you pass in the name of the locale you want to use. For example, for the es (Spanish) locale, you would use: `cronstrue.toString("* * * * *", { locale: "es" })`.

### All Locales

[Permalink: All Locales](https://www.npmjs.com/package/cronstrue#all-locales)

You can import all locales at once with `cronstrue/i18n`. This approach has the advantage of only having to load one module and having access to all supported locales. The tradeoff with this approach is a larger module (~130k, minified) that will take longer to load, particularly when sending down to a browser.

```
// Node / CommonJS
const cronstrue = require('cronstrue/i18n');

// ESM / webpack / TypeScript
import cronstrue from 'cronstrue/i18n';

// Browser
<script src="https://unpkg.com/cronstrue@latest/cronstrue-i18n.min.js" async></script>

cronstrue.toString("*/5 * * * *", { locale: "fr" }); // => Toutes les 5 minutes
cronstrue.toString("*/5 * * * *", { locale: "es" }); // => Cada 5 minutos
```

### Individual Locales

[Permalink: Individual Locales](https://www.npmjs.com/package/cronstrue#individual-locales)

You can also load the main cronstrue module and then load individual locale modules you want to have access to. This works well when you have one or more locales you know you need access to and want to minimize load time, particularly when sending down to a browser. The main cronstrue module is about 42k (minified) and each locale is about 4k (minified) in size.

```
// Node / CommonJS
const cronstrue = require('cronstrue');
require('cronstrue/locales/fr');
require('cronstrue/locales/es');

// ESM / webpack / TypeScript
import cronstrue from 'cronstrue';
import 'cronstrue/locales/fr';
import 'cronstrue/locales/es';

// Browser
<script src="https://unpkg.com/cronstrue@latest/dist/cronstrue.min.js" async></script>
<script src="https://unpkg.com/cronstrue@latest/locales/fr.min.js" async></script>
<script src="https://unpkg.com/cronstrue@latest/locales/es.min.js" async></script>

cronstrue.toString("*/5 * * * *", { locale: "fr" }); // => Toutes les 5 minutes
cronstrue.toString("*/5 * * * *", { locale: "es" }); // => Cada 5 minutos
```

### Supported Locales

[Permalink: Supported Locales](https://www.npmjs.com/package/cronstrue#supported-locales)

The following locales can be passed in for the `locale` option. Thank you to the author (shown below) of each translation!

- en - English ( [Brady Holt](https://github.com/bradymholt))
- af - Afrikaans ( [Michael van Niekerk](https://github.com/mvniekerk))
- ar - Arabic ( [Mohamed Nehad Shalabi](https://github.com/mohamednehad450))
- be - Belarusian ( [Kirill Mikulich](https://github.com/KirillMikulich))
- bg - Bulgarian ( [kamenf](https://github.com/kamenf))
- ca - Catalan ( [Francisco Javier Barrena](https://github.com/fjbarrena))
- cs - Czech ( [hanbar](https://github.com/hanbar))
- da - Danish ( [Rasmus Melchior Jacobsen](https://github.com/rmja))
- de - German ( [Michael Schuler](https://github.com/mschuler))
- es - Spanish ( [Ivan Santos](https://github.com/ivansg))
- fa - Farsi ( [A. Bahrami](https://github.com/alirezakoo))
- fi - Finnish ( [Mikael Rosenberg](https://github.com/MR77FI))
- fr - French ( [Arnaud TAMAILLON](https://github.com/Greybird))
- he - Hebrew ( [Ilan Firsov](https://github.com/IlanF))
- hr - Croatian ( [Rok Šekoranja](https://github.com/Rookxc))
- hu - Hungarian ( [Orcsity Norbert](https://github.com/Northber), Szabó Dániel)
- id - Indonesia ( [Hasan Basri](https://github.com/hasanbasri1993))
- it - Italian ( [rinaldihno](https://github.com/rinaldihno))
- ja - Japanese ( [Alin Sarivan](https://github.com/asarivan))
- ko - Korean ( [Ion Mincu](https://github.com/ionmincu))
- my - Malay (Malaysia) ( [Ikhwan Abdullah](https://github.com/leychay))
- nb - Norwegian ( [Siarhei Khalipski](https://github.com/KhalipskiSiarhei))
- nl - Dutch ( [TotalMace](https://github.com/TotalMace))
- pl - Polish ( [foka](https://github.com/foka))
- pt\_BR - Portuguese (Brazil) ( [Renato Lima](https://github.com/natenho))
- pt\_PT - Portuguese (Portugal) ( [POFerro](https://github.com/POFerro))
- ro - Romanian ( [Illegitimis](https://github.com/illegitimis))
- ru - Russian ( [LbISS](https://github.com/LbISS))
- sk - Slovakian ( [hanbar](https://github.com/hanbar))
- sl - Slovenian ( [Jani Bevk](https://github.com/jenzy))
- sw - Swahili ( [Leylow Lujuo](https://github.com/leyluj))
- sv - Swedish ( [roobin](https://github.com/roobin))
- sr - Serbian ( [Miloš Paunović](https://github.com/MilosPaunovic))
- th - Thai ( [Teerapat Prommarak](https://github.com/xeusteerapat))
- tr - Turkish ( [Mustafa SADEDİL](https://github.com/sadedil))
- uk - Ukrainian ( [Taras](https://github.com/tbudurovych))
- vi - Vietnamese ( [Nguyen Tan Phap](https://github.com/rikkapro0128))
- zh\_CN - Chinese (Simplified) ( [Star Peng](https://github.com/starpeng))
- zh\_TW - Chinese (Traditional) ( [Ricky Chiang](https://github.com/metavige))

## Frequently Asked Questions

[Permalink: Frequently Asked Questions](https://www.npmjs.com/package/cronstrue#frequently-asked-questions)

1. The cron expression I am passing in is not valid and this library is giving strange output. What should I do?

This library does not do full validation of cron expressions and assumes the expression passed in is valid. If you need to validate an expression consider using a library like [cron-parser](https://www.npmjs.com/package/cron-parser). Example validation with cron-parser:


```
const cronParser = require("cron-parser");
const cronstrue = require("cronstrue");

const expression = "* * * * * *";

// Validate expression first
let isCronValid = true;
try { cronParser.parseExpression(expression) } catch(e) { isCronValid = false; }

// If valid, then pass into cRonstrue
if (isCronValid) {
     console.log(cronstrue.toString("* * * * *"));
}
```

2. Can cRonstrue output the next occurrence of the cron expression?

No, cRonstrue does not support this. This library simply describes a cron expression that is passed in.


## Sponsors

[Permalink: Sponsors](https://www.npmjs.com/package/cronstrue#sponsors)

Thank you to the following sponsors of this project!

[![robjtede](https://github.com/microsoft.png)](https://github.com/microsoft)[![robjtede](https://github.com/github.png)](https://github.com/github)[![robjtede](https://github.com/DevUtilsApp.png)](https://github.com/DevUtilsApp)[![robjtede](https://github.com/getsentry.png)](https://github.com/getsentry)[![robjtede](https://github.com/KevinWang15.png)](https://github.com/KevinWang15)[![robjtede](https://github.com/timheuer.png)](https://github.com/timheuer)

## License

[Permalink: License](https://www.npmjs.com/package/cronstrue#license)

cRonstrue is freely distributable under the terms of the [MIT license](https://github.com/bradymholt/cronstrue/blob/main/LICENSE).

## Readme

### Keywords

- [cron](https://www.npmjs.com/search?q=keywords:cron)
- [cronjob](https://www.npmjs.com/search?q=keywords:cronjob)
- [crontab](https://www.npmjs.com/search?q=keywords:crontab)
- [schedule](https://www.npmjs.com/search?q=keywords:schedule)
- [parser](https://www.npmjs.com/search?q=keywords:parser)
- [cron expression](https://www.npmjs.com/search?q=keywords:%22cron%20expression%22)
- [cron description](https://www.npmjs.com/search?q=keywords:%22cron%20description%22)
- [pretty cron](https://www.npmjs.com/search?q=keywords:%22pretty%20cron%22)
- [cron for humans](https://www.npmjs.com/search?q=keywords:%22cron%20for%20humans%22)
- [cron translated](https://www.npmjs.com/search?q=keywords:%22cron%20translated%22)
- [cron english](https://www.npmjs.com/search?q=keywords:%22cron%20english%22)
- [cron schedule](https://www.npmjs.com/search?q=keywords:%22cron%20schedule%22)
- [cron english](https://www.npmjs.com/search?q=keywords:%22cron%20english%22)
- [cron schedule](https://www.npmjs.com/search?q=keywords:%22cron%20schedule%22)

## Package Sidebar

### Install

`npm i cronstrue`

### Repository

[Gitgithub.com/bradymholt/cronstrue](https://github.com/bradymholt/cronstrue)

### Homepage

[github.com/bradymholt/cronstrue](https://github.com/bradymholt/cronstrue)

### DownloadsWeekly Downloads

1,710,431

### Version

3.14.0

### License

MIT

### Unpacked Size

1.21 MB

### Total Files

139

### Issues

[1](https://github.com/bradymholt/cronstrue/issues)

### Pull Requests

[0](https://github.com/bradymholt/cronstrue/pulls)

### Last publish

15 days ago

### Collaborators

- [![bradymholt](https://www.npmjs.com/npm-avatar/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdmF0YXJVUkwiOiJodHRwczovL3MuZ3JhdmF0YXIuY29tL2F2YXRhci9hZTQ3NGRkNGEwNzRmZDIyZTg5N2M0YzU0NzcwYzA1YT9zaXplPTEwMCZkZWZhdWx0PXJldHJvIn0.5Mj9HB09P9JAIDGgV8lZJuJXWJ1x8F-xX-qXO17C4ac)](https://www.npmjs.com/~bradymholt)

bradymholt


[**Analyze security** with Socket](https://socket.dev/npm/package/cronstrue) [**Check bundle size**](https://bundlephobia.com/package/cronstrue) [**View package health**](https://snyk.io/advisor/npm-package/cronstrue) [**Explore dependencies**](https://npmgraph.js.org/?q=cronstrue)

[**Report** malware](https://www.npmjs.com/support?inquire=security&security-inquire=malware&package=cronstrue&version=3.14.0)

## Footer

[Visit npm GitHub page](https://github.com/npm)

[GitHub](https://github.com/)

### Support

- [Help](https://docs.npmjs.com/)
- [Advisories](https://github.com/advisories)
- [Status](http://status.npmjs.org/)
- [Contact npm](https://www.npmjs.com/support)

### Company

- [About](https://www.npmjs.com/about)
- [Blog](https://github.blog/tag/npm/)
- [Press](https://www.npmjs.com/press)

### Terms & Policies

- [Policies](https://www.npmjs.com/policies/)
- [Terms of Use](https://www.npmjs.com/policies/terms)
- [Code of Conduct](https://www.npmjs.com/policies/conduct)
- [Privacy](https://www.npmjs.com/policies/privacy)

Viewing cronstrue version 3.14.0