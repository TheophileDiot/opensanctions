from pprint import pprint  # noqa
from ftmstore.memorious import EntityEmitter
from urllib.parse import urljoin

from opensanctions import constants

SEARCH_URL = "https://op.europa.eu/en/web/who-is-who/search-results?p_p_id=eu_europa_publications_portlet_search_result_summary_SearchResultSummaryPortlet_INSTANCE_R2s6PcS1Wa4m&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&facet.collection=EUDir&WIW_SEARCH_TYPE=SIMPLE&sortBy=RELEVANCE-DESC&SEARCH_TYPE=SIMPLE&resultsPerPage=50"

SEXES = {
    "Mr": constants.MALE,
    "Ms": constants.FEMALE,
}


def parse(context, data):
    emitter = EntityEmitter(context)
    url = data.get('url')
    page_number = data.get('page number')
    with context.http.rehash(data) as res:
        doc = res.html
        for li in doc.findall('.//div[@class="row portlet-column"]//ul/li[@class="list-item first clearfix row"]'):
            if li.find('.//div[@class="entity-hit search-person-hit "]') is not None:
                person_title = li.find('.//div[@class="wiw-person-title"]/a')
                memberships = li.findall(
                    './/div[@class="wiw-person-personHitMemberships"]/div')
                contacts = li.findall(
                    './/div[@class="entity-combined-address"]/div')

                name = person_title.find('./span').text.split()
                title = name[0]
                name = name[1::]
                first_name = ''
                for x in range(len(name)):
                    if (first_name + ' ' + name[x]).istitle():
                        first_name = "{} {}".format(
                            first_name, name[x]).strip()
                        last_name = " ".join(name[x + 1::])

                list_memberships = []
                for membership in memberships:
                    infos = membership.findall('./div')
                    list_memberships.append(", ".join(["{}: {}".format(info.attrib['class'].split(
                        '-')[-1], info.findall('./span')[-1].text) for info in infos]))

                list_emails = []
                list_websites = []
                list_phones = []
                for contact in contacts:
                    for email in contact.findall('./div[@class="address-email-section"]/div'):
                        email = email.find('./a')
                        if email is not None:
                            list_emails.append(email.attrib['href'][7::])
                    for website in contact.findall('./div[@class="address-email-section"]/span'):
                        website = website.find('./a')
                        if website is not None:
                            list_websites.append(website.attrib['href'])
                    for phone in contact.findall('./div[@class="address-phones-section"]//div[@class="address-details-container"]/div'):
                        phone = phone.find('./a')
                        if phone is not None:
                            list_phones.append(phone.attrib['href'][4::])

                name = " ".join(name)

                entity = emitter.make("Person")
                entity.make_id(
                    title, name, person_title.attrib['href'], url, str(page_number))

                entity.add('name', name)
                entity.add('sourceUrl', person_title.attrib['href'])
                entity.add('publisher', "EU Whoiswho")
                entity.add('publisherUrl', url)

                entity.add(
                    'email', list_emails if list_emails else 'no emails')
                entity.add(
                    'phone', list_phones if list_phones else 'no phones')
                entity.add(
                    'website', list_websites if list_websites else 'no websites')

                entity.add('title', title)
                entity.add('firstName', first_name)
                entity.add('lastName', last_name)
                entity.add('position', list_memberships)
                entity.add('gender', SEXES.get(title))

                emitter.emit(entity)
    emitter.finalize()


def index(context, data):
    with context.http.rehash(data) as res:
        doc = res.html
        num_results = doc.find(
            './/span[@class="results-number-info"]').text.strip()
        num_results = int(num_results[9:num_results.find(' r')])
        for x in range(1, num_results, 50):
            url = "{}{}".format(SEARCH_URL, "&startRow={}".format(x))
            context.log.info("Crawling page: {} ({})".format(
                "page {}".format(round(x / 50) + 1), url))
            context.emit(data={"url": url, "page number": round(x / 50) + 1})
