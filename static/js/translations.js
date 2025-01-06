// translations.js

const translations = {
    en: {
        welcome: "WELCOME TO THE GREEN SOLUTION",
        welcome_1: "There is a way to reduce this plastic menace by bringing in new and innovative products which are part of nature and doesn’t harm the environment. We are dedicated to delivering products that are 100% sustainable, compostable and eco-friendly.",
        welcome_2: "We provide high-quality products at affordable prices as compared to our peers. We make this possible only because we are an enthusiastic team of material engineers, who are involved in procuring the products from the source to delivering it directly to the customer. Due to our material knowledge, we can maintain and supply high-quality products adhering to German standards.",
        welcome_3: "In addition, we can also provide customized solutions to our customers according to their business needs. We take pleasure in ensuring that we are their one-stop solution for choosing to move towards a greener life.",
        feature_pro: "Featured Products",
        cus_says: "What Our Customer Says?",
        post: "Our Latest Posts",
        free_deli: "Free Delivery on Orders above 25 €",
        offer: "Get 20% Off Your Next Order",
        home: "Home"
    },
    de: {
        welcome: "WILLKOMMEN BEI DER GRÜNEN LÖSUNG",
        welcome_1: "Es gibt eine Möglichkeit, diese Plastikgefahr zu reduzieren, indem man neue und innovative Produkte einführt, die Teil der Natur sind und die Umwelt nicht schädigen. Wir sind bestrebt, Produkte zu liefern, die zu 100 % nachhaltig, kompostierbar und umweltfreundlich sind.",
        welcome_2: "Im Vergleich zu unseren Mitbewerbern bieten wir qualitativ hochwertige Produkte zu erschwinglichen Preisen an. Wir machen dies nur möglich, weil wir ein begeistertes Team von Materialingenieuren sind, die an der Beschaffung der Produkte von der Quelle bis zur direkten Lieferung an den Kunden beteiligt sind. Aufgrund unserer Materialkenntnisse können wir qualitativ hochwertige Produkte nach deutschen Standards warten und liefern.",
        welcome_3: "Darüber hinaus können wir unseren Kunden auch maßgeschneiderte Lösungen entsprechend ihren Geschäftsanforderungen anbieten. Es ist uns eine Freude, sicherzustellen, dass wir die Komplettlösung für Sie sind, wenn Sie sich für ein umweltfreundlicheres Leben entscheiden.",
        feature_pro: "Ausgewählte Produkte",
        cus_says: "Was unsere Kunden sagen?",
        post: "Unsere neuesten Beiträge",
        free_deli: "Kostenlose Lieferung bei Bestellungen über 25 €",
        offer: "Erhalten Sie 20 % Rabatt auf Ihre nächste Bestellung",
        home: "Startsiete"
    }
};

// Function to switch language and store it in localStorage
function switchLanguage(lang) {
    // Store selected language in localStorage
    localStorage.setItem('selectedLanguage', lang);

    // Update text content of elements based on selected language
    document.getElementById("welcome").textContent = translations[lang].welcome;
    document.getElementById("welcome_1").textContent = translations[lang].welcome_1;
    document.getElementById("welcome_2").textContent = translations[lang].welcome_2;
    document.getElementById("welcome_3").textContent = translations[lang].welcome_3;
    document.getElementById("feature_pro").textContent = translations[lang].feature_pro;
    document.getElementById("cus_says").textContent = translations[lang].cus_says;
    document.getElementById("post").textContent = translations[lang].post;
    document.getElementById("free_deli").textContent = translations[lang].free_deli;
    document.getElementById("offer").textContent = translations[lang].offer;
    document.getElementById("home").textContent = translations[lang].home;

}

// Function to load the saved language from localStorage when the page loads
function loadLanguage() {
    // Check if a language is stored in localStorage
    const savedLanguage = localStorage.getItem('selectedLanguage') || 'de';  // Default to English if not found
    switchLanguage(savedLanguage);
}
