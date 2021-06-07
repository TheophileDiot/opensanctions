import json
from opensanctions import constants

TRANSLATE = {"Commentaire": "comment", "Lieu": "Place",
             "Adresse": "Address", "Pays": "Country", "Alias": "Alias", "NumeroCarte": "idNumber", "Identification": "Identification"}
NATURES = {"Personne physique": "Person",
           "Personne morale": "Company", "Navire": "Vessel"}
GENDERS = {"Masculin": constants.MALE, "Feminin": constants.FEMALE}


def rearange(data: list):
    if len(data) == 0:
        data = None
    elif len(data) == 1:
        data = data[0]
    return data


def parse_reference(context, id: str, schema: str, name: str, values: list):
    entity = context.make(schema)
    entity.make_id(id)
    entity.add("name", name)

    # Thing
    address = []
    country = []
    alias = []

    # LegalEntity
    email = []
    phone = []
    website = []
    idNumber = []

    # Person
    title = []
    firstName = []
    birthDate = None
    birthPlace = []
    nationality = []
    gender = None
    passportNumber = []

    # Company
    registrationNumber = []

    # Vessel
    imoNumber = None

    for val in values:
        if val["TypeChamp"] == "ADRESSE_PP" or val["TypeChamp"] == "ADRESSE_PM":
            address = [{TRANSLATE[row]: data[row] for row in data}
                       for data in val["Valeur"]]
            country = [data["Pays"] for data in val["Valeur"]]
        elif val["TypeChamp"] == "ALIAS":
            alias = [data["Alias"] for data in val["Valeur"]]
        elif val["TypeChamp"] == "AUTRE_IDENTITE":
            idNumber = [{TRANSLATE[row]: data[row]
                         for row in data} for data in val["Valeur"]]

        if schema == "Person":
            if val["TypeChamp"] == "TITRE":
                title = [data["Titre"] for data in val["Valeur"]]
            elif val["TypeChamp"] == "PRENOM":
                firstName = [data["Prenom"] for data in val["Valeur"]]
            elif val["TypeChamp"] == "DATE_DE_NAISSANCE":
                if val["Valeur"][0]["Mois"] != '':
                    birthDate = "{}/{}/{}".format(
                        val["Valeur"][0]["Annee"], val["Valeur"][0]["Mois"], val["Valeur"][0]["Jour"])
                else:
                    birthDate = val["Valeur"][0]["Annee"]
            elif val["TypeChamp"] == "LIEU_DE_NAISSANCE":
                birthPlace = [{TRANSLATE[row]: data[row] for row in data}
                              for data in val["Valeur"]]
            elif val["TypeChamp"] == "NATIONALITE":
                nationality = [data["Pays"] for data in val["Valeur"]]
            elif val["TypeChamp"] == "SEXE":
                gender = val["Valeur"][0]["Sexe"]
            elif val["TypeChamp"] == "PASSEPORT":
                passportNumber = [data["NumeroPasseport"]
                                  for data in val["Valeur"]]
        elif schema == "Company":
            if val["TypeChamp"] == "COURRIEL":
                email = [data["Courriel"] for data in val["Valeur"]]
            elif val["TypeChamp"] == "TELEPHONE":
                phone = [data["Telephone"] for data in val["Valeur"]]
            elif val["TypeChamp"] == "SITE_INTERNET":
                website = [data["SiteInternet"] for data in val["Valeur"]]
            elif val["TypeChamp"] == "IDENTIFICATION":
                registrationNumber = [{TRANSLATE[row]: data[row]
                                       for row in data} for data in val["Valeur"]]
        elif schema == "Vessel":
            if val["TypeChamp"] == "NUMERO_OMI":
                imoNumber = val["Valeur"][0]["NumeroOMI"]

    # delete every empty string and duplicates
    country = list(dict.fromkeys(list(filter(None, country))))

    # rearange data
    address = rearange(address)
    country = rearange(country)
    alias = rearange(alias)

    if schema == "Person":
        title = rearange(title)
        firstName = rearange(firstName)
        birthPlace = rearange(birthPlace)
        nationality = rearange(nationality)
        passportNumber = rearange(passportNumber)
        idNumber = rearange(idNumber)
    elif schema == "Company":
        email = rearange(email)
        phone = rearange(phone)
        website = rearange(website)
        registrationNumber = rearange(registrationNumber)

    # add data to entity
    entity.add("address", address)
    entity.add("country", country)
    entity.add("alias", alias)

    if schema == "Person":
        entity.add("title", title)
        entity.add("firstName", firstName)
        entity.add("lastName", name)
        entity.add("birthDate", birthDate)
        entity.add("birthPlace", birthPlace)
        entity.add("nationality", nationality)
        entity.add("gender", gender)
        entity.add("passportNumber", passportNumber)
        entity.add("idNumber", idNumber)
    elif schema == "Company":
        entity.add("email", email)
        entity.add("phone", phone)
        entity.add("website", website)
        entity.add("registrationNumber", registrationNumber)
    elif schema == "Vessel":
        entity.add("imoNumber", imoNumber)

    context.emit(entity)


def crawl(context):
    res = context.http.get(context.dataset.data.url)
    data = json.loads(res.content)
    x = 0
    for val in data["Publications"]["PublicationDetail"]:
        parse_reference(context, val.pop("IdRegistre"),
                        NATURES[val.pop("Nature")], val.pop("Nom"), val["RegistreDetail"])
