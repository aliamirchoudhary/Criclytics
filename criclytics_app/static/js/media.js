/* Curated public media, bound to Cricsheet identities. No name-based photo guessing. */
(function () {
  'use strict';
  const {node} = window.CriclyticsDOM;
  const flags = Object.freeze({
    "Philippines": "ph",
    "Vanuatu": "vu",
    "Ghana": "gh",
    "Botswana": "bw",
    "Guernsey": "gg",
    "Norway": "no",
    "Thailand": "th",
    "Maldives": "mv",
    "Cayman Islands": "ky",
    "Portugal": "pt",
    "Gibraltar": "gi",
    "Bhutan": "bt",
    "Iran": "ir",
    "Belgium": "be",
    "Luxembourg": "lu",
    "Czech Republic": "cz",
    "Isle of Man": "im",
    "Bulgaria": "bg",
    "Romania": "ro",
    "Austria": "at",
    "Greece": "gr",
    "Serbia": "rs",
    "Malta": "mt",
    "France": "fr",
    "Sweden": "se",
    "Rwanda": "rw",
    "Finland": "fi",
    "Hungary": "hu",
    "Estonia": "ee",
    "Cyprus": "cy",
    "Switzerland": "ch",
    "Seychelles": "sc",
    "Malawi": "mw",
    "Lesotho": "ls",
    "Swaziland": "sz",
    "Eswatini": "sz",
    "Sierra Leone": "sl",
    "Mozambique": "mz",
    "Cameroon": "cm",
    "Belize": "bz",
    "Bahamas": "bs",
    "Panama": "pa",
    "Israel": "il",
    "Turkey": "tr",
    "Croatia": "hr",
    "Slovenia": "si",
    "Cook Islands": "ck",
    "Fiji": "fj",
    "Samoa": "ws",
    "Japan": "jp",
    "Indonesia": "id",
    "South Korea": "kr",
    "Mali": "ml",
    "St Helena": "sh",
    "Gambia": "gm",
    "China": "cn",
    "Myanmar": "mm",
    "Mongolia": "mn",
    "Chile": "cl",
    "Mexico": "mx",
    "Cambodia": "kh",
    "Costa Rica": "cr",
    "Brazil": "br",
    "Ivory Coast": "ci",
    "Suriname": "sr",
    "Turks and Caicos Island": "tc",
    "Timor-Leste": "tl",
    "Zambia": "zm",
    "India": "in",
    "Pakistan": "pk",
    "Australia": "au",
    "England": "gb-eng",
    "South Africa": "za",
    "New Zealand": "nz",
    "Sri Lanka": "lk",
    "Bangladesh": "bd",
    "Afghanistan": "af",
    "Ireland": "ie",
    "Zimbabwe": "zw",
    "Netherlands": "nl",
    "Nepal": "np",
    "United States of America": "us",
    "United States": "us",
    "USA": "us",
    "Canada": "ca",
    "United Arab Emirates": "ae",
    "UAE": "ae",
    "Oman": "om",
    "Scotland": "gb-sct",
    "Kenya": "ke",
    "Uganda": "ug",
    "Namibia": "na",
    "Papua New Guinea": "pg",
    "Hong Kong": "hk",
    "Jersey": "je",
    "Bermuda": "bm",
    "Italy": "it",
    "Germany": "de",
    "Denmark": "dk",
    "Malaysia": "my",
    "Singapore": "sg",
    "Kuwait": "kw",
    "Bahrain": "bh",
    "Qatar": "qa",
    "Saudi Arabia": "sa",
    "Nigeria": "ng",
    "Tanzania": "tz",
    "Argentina": "ar",
    "Spain": "es"
});
  const portraits = Object.freeze({
    'player:cricsheet:ba607b88':{slug:'kohli',file:'kohli.jpg',name:'Virat Kohli',record:'V Kohli',team:'India',author:'Anand Anil',license:'CC BY-SA 4.0',licenseURL:'https://creativecommons.org/licenses/by-sa/4.0/',source:'https://commons.wikimedia.org/wiki/File:Virat_Kohli_portrait.jpg'},
    'player:cricsheet:8a75e999':{slug:'babar',file:'babar.png',name:'Babar Azam',record:'Babar Azam',team:'Pakistan',author:'BBC Urdu',license:'CC BY 3.0',licenseURL:'https://creativecommons.org/licenses/by/3.0/',source:'https://commons.wikimedia.org/wiki/File:Babar_Azam_in_2020.png'}
  });
  function initials(name) { return String(name || '?').split(/\s+/).filter(Boolean).slice(0,2).map(s => s[0]).join('').toUpperCase(); }
  function imageBox(name, source, className, alt) {
    const wrap = node('span', initials(name), className);
    wrap.setAttribute('role','img'); wrap.setAttribute('aria-label',alt || name);
    if (source) {
      const image = node('img'); image.alt = ''; image.loading = className === 'ui-flag' ? 'eager' : 'lazy'; image.decoding = 'async';
      image.addEventListener('error', () => {
        wrap.replaceChildren(document.createTextNode(initials(name)));
        wrap.classList.add('ui-image-fallback');
        wrap.setAttribute('aria-label',name+' · image unavailable');
      }, {once:true});
      image.src = source; wrap.replaceChildren(image);
    }
    return wrap;
  }
  function flag(name) {
    // West Indies is a regional cricket team; never substitute a national flag.
    return imageBox(name, flags[name] ? '/static/images/flags/'+flags[name]+'.svg' : null, 'ui-flag',name+' team');
  }
  function portrait(player, large) {
    const media = portraits[player.identity_id];
    return imageBox(player.name, media ? '/static/images/players/'+media.file : null,
      'ui-player-avatar'+(large ? ' ui-player-avatar-large' : ''), media ? media.name+' portrait' : player.name+' \u00b7 photo unavailable');
  }
  function credit(identity) {
    const media = portraits[identity]; if (!media) return null;
    const line = node('small',null,'ui-photo-credit'), source = node('a',media.author), license = node('a',media.license);
    source.href = media.source; license.href = media.licenseURL;
    line.append('Photo: ',source,' / ',license,' \u00b7 display crop'); return line;
  }
  window.CriclyticsMedia = Object.freeze({flag,portrait,credit,portraits});
}());
