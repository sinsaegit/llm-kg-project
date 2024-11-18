import openai
from constants import API_KEY
from openai import OpenAI
from rdflib import Graph, Namespace
import json

openai.api_key = API_KEY  # NOTE: Change this API_KEY to your own as the original key is stored safely elsewhere.

client = OpenAI(api_key=openai.api_key)


class LanguageToGraph:
    def __init__(self, model="gpt-4o-mini", api_key=None):
        self.model = model
        self.entities = None
        self.message = None
        if api_key:
            openai.api_key = api_key
        self.graph = Graph()
        self.namespace = Namespace("http://example.org#")  # Define your namespace
        self.graph.bind("ex", self.namespace)

        self.entity_prompt = (
            f"Dette er meldingene: {self.message}."
            "Du skal finne viktige entiteter som for eksempel: lokasjoner, hendelser, kjøretøy og mennesker med mer, fra følgende melding."
            "Forsøk å ikke bruke pronomen, men heller entitene pronomenene viser til."
            "Bare inkluder de identifsierte entitene, uten noe ekstra besvarelse."
        )
        self.relationship_prompt = (
            f"Dette er meldingen: {self.message}. Dette er meldingens entiteter: {self.entities}."
            "Bruk meldingen og identifiserte entiteter til å avgjøre relasjoner. "
            "Formater hver enkelt relasjon som tripler/ontologier på formen (Subjekt, Predikat, Objekt)."
            "Husk at predikater skal ha underscore mellom seg. "
            "Bare inkluder de identifsierte triplene med relasjonen du fant som predikat, uten noe ekstra besvarelse."
        )

        self.few_shot_entities = """
Input: 24b43w (Follesevegen, Askøy, 2024-08-12T05:50:23.2538153+00:00): Politiet har komme fram til staden. Materielle skadar i front av bilen. Bilberger er bestilte og på veg. Trafikken flyt greitt på staden.
Output: {
  "ID": "24b43w",
  "Timestamp": "2024-08-12T05:50:23.2538153+00:00",
  "Location": "Follesevegen, Askøy",
  "Entities": [
    {"Entiteter": "Bilen", "Type": "Kjøretøy"},
    {"Entiteter": "Materielle skadar", "Type": "Hendelse"},
    {"Entiteter": "Bilberger", "Type": "Service"},
    {"Entiteter": "Politiet", "Type": "Organisasjon"}
  ]
}

Input: 24c8x7 (Fjøsanger, Bergen, 2024-08-11T08:18:25.5956991+00:00): Kl. 08:35 Melding om kjøring i trolig ruspåvirket tilstand. Kjørte bl.a. på felgen. Politiet stanset kjøretøy i sidegate til Fjøsangervegen. To personer i bilen. Begge fremstår ruset. Fører fremstilt for blodprøve på Bergen Legevakt. Sak opprettet. 
Output: {
  "ID": "24c8x7",
  "Timestamp": "2024-08-11T08:18:25.5956991+00:00",
  "Location": "Fjøsanger, Bergen",
  "Entities": [
    {"Entiteter": "Kjøring i ruspåvirket tilstand", "Type": "Hendelse"},
    {"Entiteter": "Felgen", "Type": "Kjøretøy-del"},
    {"Entiteter": "Kjøretøy", "Type": "Kjøretøy"},
    {"Entiteter": "Politiet", "Type": "Organisasjon"},
    {"Entiteter": "To personer", "Type": "Personer"},
    {"Entiteter": "Bergen Legevakt", "Type": "Sted"}
  ]
}

Input: 24w0z5 (Danmarksplass, Bergen, 2024-08-14T06:07:37.2057264+00:00): 3 biler involvert i trafikkuhell. Kun meldt om materielle skader. Skaper køer mot Bergen sør. Politiet er på vei til stedet. 
Output: {
  "ID": "24w0z5",
  "Timestamp": "2024-08-14T06:07:37.2057264+00:00",
  "Location": "Danmarksplass, Bergen",
  "Entities": [
    {"Entiteter": "3 biler", "Type": "Kjøretøy"},
    {"Entiteter": "Trafikkuhell", "Type": "Hendelse"},
    {"Entiteter": "Materielle skader", "Type": "Skade"},
    {"Entiteter": "Bergen sør", "Type": "Sted"},
    {"Entiteter": "Politiet", "Type": "Organisasjon"}
  ]
}
"""
        self.few_shot_relations = """
Input: [Melding: "24b43w (Follesevegen, Askøy, 2024-08-12T05:50:23.2538153+00:00): Politiet har komme fram til staden. Materielle skadar i front av bilen. Bilberger er bestilte og på veg. Trafikken flyt greitt på staden.",
        Entiteter: {
        "ID": "24b43w",
        "Timestamp": "2024-08-12T05:50:23.2538153+00:00",
        "Lokasjon": "Follesevegen, Askøy",
        "Entiteter": [
            {"Entiteter": "Bilen", "Type": "Kjøretøy"},
            {"Entiteter": "Materielle skadar", "Type": "Hendelse"},
            {"Entiteter": "Bilberger", "Type": "Service"},
            {"Entiteter": "Politiet", "Type": "Organisasjon"}
        ]}
Output: 
[
(Hendelse, har_id, 24b43w)
(Hendelse, har_tid, 2024-08-12T05:50:23.2538153+00:00)
(Hendelse, skjedde_på, Follesevegen, Askøy)
(Hendelse, har_entiteter, Entiteter)
(Hendelse, del_av_forløp, (Politiet, ankom, Follesvegen, Askøy))
(Hendelse, del_av_forløp, (Materielle skadar, på, Bilen))
(Hendelse, del_av_forløp, (Bilberger, er, bestilt))
(Hendelse, del_av_forløp, (Trafikken, flyter, greit))
]


Input: [Melding: "24c8x7 (Fjøsanger, Bergen, 2024-08-11T08:18:25.5956991+00:00): Kl. 08:35 Melding om kjøring i trolig ruspåvirket tilstand. Kjørte bl.a. på felgen. Politiet stanset kjøretøy i sidegate til Fjøsangervegen. To personer i bilen. Begge fremstår ruset. Fører fremstilt for blodprøve på Bergen Legevakt. Sak opprettet.",
        Entiteter:{
        "ID": "24c8x7",
        "Timestamp": "2024-08-11T08:18:25.5956991+00:00",
        "Lokasjon": "Fjøsanger, Bergen",
        "Hendelse": " Kl. 08:35 Melding om kjøring i trolig ruspåvirket tilstand. Kjørte bl.a. på felgen. Politiet stanset kjøretøy i sidegate til Fjøsangervegen. To personer i bilen. Begge fremstår ruset. Fører fremstilt for blodprøve på Bergen Legevakt. Sak opprettet. "
        "Entiteter": [
            {"Entiteter": "Kjøring i ruspåvirket tilstand", "Type": "Hendelse"},
            {"Entiteter": "Felgen", "Type": "Kjøretøy-del"},
            {"Entiteter": "Kjøretøy", "Type": "Kjøretøy"},
            {"Entiteter": "Politiet", "Type": "Organisasjon"},
            {"Entiteter": "To personer", "Type": "Personer"},
            {"Entiteter": "Bergen Legevakt", "Type": "Sted"}
        ]}
Output: 
[
(Hendelse, har_id, 24c8x7),
(Hendelse, har_tid, 2024-08-11T08:18:25.5956991+00:00),
(Hendelse, skjedde_på, Fjøsanger, Bergen),
(Hendelse, har_entiteter, Entiteter),
(Hendelse, del_av_forløp, (Politiet, stanset, Kjøretøy, i sidegate til Fjøsangervegen)),
(Hendelse, del_av_forløp, (Kjøring i ruspåvirket tilstand, inkluderte, Felgen)),
(Hendelse, del_av_forløp, (To personer, fremstår som, ruset)),
(Hendelse, del_av_forløp, (Fører, fremstilt for blodprøve, på Bergen Legevakt)),
(Hendelse, del_av_forløp, (Politiet, opprettet, Sak))
]


Input: [Meldinger: "24w0z5 (Danmarksplass, Bergen, 2024-08-14T06:07:37.2057264+00:00): 3 biler involvert i trafikkuhell. Kun meldt om materielle skader. Skaper køer mot Bergen sør. Politiet er på vei til stedet.",
        Entiteter:{
  "ID": "24w0z5",
  "Timestamp": "2024-08-14T06:07:37.2057264+00:00",
  "Lokasjon": "Danmarksplass, Bergen",
  "Hendelse"
  "Entiteter": [
    {"Entiteter": "3 biler", "Type": "Kjøretøy"},
    {"Entiteter": "Trafikkuhell", "Type": "Hendelse"},
    {"Entiteter": "Materielle skader", "Type": "Skade"},
    {"Entiteter": "Bergen sør", "Type": "Sted"},
    {"Entiteter": "Politiet", "Type": "Organisasjon"}
  ]}
Output:
[
(Hendelse, har_id, 24w0z5),
(Hendelse, har_tid, 2024-08-14T06:07:37.2057264+00:00),
(Hendelse, skjedde_på, Danmarksplass, Bergen),
(Hendelse, har_entiteter, Entiteter),
(Hendelse, del_av_forløp, (3 biler, involvert i, Trafikkuhell)),
(Hendelse, del_av_forløp, (Trafikkuhell, resulterte i, Materielle skader)),
(Hendelse, del_av_forløp, (Trafikkuhell, skaper, køer mot Bergen sør)),
(Hendelse, del_av_forløp, (Politiet, er på vei til, stedet))
]
"""

    def load_msg(self, filename):
        messages = []
        if filename.endswith(".txt"):
            with open(filename, "r", encoding="utf-8") as file:
                content = file.read().split("\n")
                for line in content:
                    if line.strip():
                        messages.append(line.strip())

        if "trafikktekster" not in filename:
            self.Entiteter_prompt = self.revise_Entiteter_prompt(messages)
            self.relationship_prompt = self.revise_Entiteter_prompt(messages)

        return messages

    def revise_Entiteter_prompt(self, messages):
        sample_messages = messages[:3]

        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du er en assisten trent til å tilpasse promptinstruksjoner for datainnsamling i Knowledge Graphs.",
                },
                {
                    "role": "user",
                    "content": (
                        "Jeg vil at du skal oppdatere en prompt for Named Entiteter Recognition basert på de følgende meldingene.\n\n"
                        f"Meldinger: {', '.join(sample_messages)}\n\n"
                        f"Tilpass ny prompt slik at den ligner på den forrige prompten: {self.Entiteter_prompt}\n\n"
                    ),
                },
            ],
            temperature=0.7,
        )

        # Update the Entiteter prompt with GPT response
        self.Entiteter_prompt = completion.choices[0].message.content.strip()

    def revise_relationship_prompt(self, messages):
        sample_messages = messages[:3]

        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du er en assistent trent til å tilpasse promptinstruksjoner for datainnsamling i Knowledge Graphs.",
                },
                {
                    "role": "user",
                    "content": (
                        "Jeg vil at du skal oppdatere en prompt for Relasjonsekstraksjon basert på de følgende meldingene.\n\n"
                        f"Meldinger: {', '.join(sample_messages)}\n\n"
                        f"Tilpass ny prompt slik at den ligner på den forrige prompten: {self.relationship_prompt}\n\n"
                    ),
                },
            ],
            temperature=0.7,
        )

        # Update the relationship prompt with GPT response
        self.relationship_prompt = completion.choices[0].message.content.strip()

    def extract_entities_from_text(self, text):
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du er en assistent trent til å gjennomføre Named Entiteter Recognition-oppgaver for Knowledge Graphs basert på meldingen og tilhørende entiteter fra meldigen.\n"
                    "Du skal alltid produsere en hovedentitet som kan binde entietene. Eksempelvis er hele meldingen en hendelse og om det er mulig, identifiser en ID-kode. Returner som en dictionary som kan enkelt behandles med eval()."
                    f"Her er noen few-shot eksempler: {self.few_shot_entities}\n",
                },
                {
                    "role": "user",
                    "content": (f"{self.entity_prompt}\n\n" f"Tekst:\n{text}\n\n"),
                },
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()

    def extract_relationships_from_text(self, text, entities):
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du er en assistent trent til å gjennomføre Relation Extraction-oppgaver basert på meldingen du mottar og entiter som som du mottar, slik at du kan produsere Kunnskapsgrafer med ontolgier.\n"
                    "Du skal alltid identifisere en ID om det finnes og hele meldingen skal være indetifsert som en hendelse. Returner som en liste som kan enkelt leses med eval(). Her er noen few-shot eksempler:\n"
                    f"{self.few_shot_relations}",
                },
                {
                    "role": "user",
                    "content": (
                        f"{self.relationship_prompt}\n\n"
                        f"Tekst:\n{text}\n\n"
                        f"Entiteter:\n{entities}\n\n"
                    ),
                },
            ],
            temperature=0.8,
        )
        return completion.choices[0].message.content.strip()

    def parse_data(data):
        for item in data:
            if isinstance(item.get('entities'), str):
                try:
                    item['entities'] = json.loads(item['entities'])
                except json.JSONDecodeError as e:
                    print(f"Encountered an issue: {e}")
            if isinstance(item.get('relationships'), str):
                try:
                    relationships_str = item['relationships'].replace("(", "[").replace(")", "]")
                    item['relationships'] = eval(relationships_str)
                except Exception as e:
                    print(f"Error decoding relationships: {e}")
        return data


    def process_messages(self, messages):
        knowledge_graphs = []

        for i, message in enumerate(messages):
            print("-------------------------------------------")
            print(message, "\n")

            entities = self.extract_entities_from_text(message)
            print(f"Entiteter i melding {i+1}:\n{entities}\n")

            relationships = self.extract_relationships_from_text(message, entities)
            print(f"Relasjoner i melding {i+1}:\n{relationships}\n")

            knowledge_graph = {
                "message": message,
                "entities": entities,
                "relationships": relationships,
            }
            knowledge_graphs.append(knowledge_graph)

        return knowledge_graphs


ltg = LanguageToGraph(model="gpt-4o-mini", api_key=openai.api_key)
directory_path = "trafikktekster-20240814.txt"
messages = ltg.load_msg(directory_path)

testset_messages = messages[:2]
knowledge_graphs = ltg.process_messages(testset_messages)
# for i in knowledge_graphs:
#     print(i, "\n\n")  # print(testset_messages)
def parse_data(data):
    for item in data:
        # Convert entities field from JSON string to Python dictionary
        if isinstance(item.get('entities'), str):
            try:
                item['entities'] = json.loads(item['entities'])
            except json.JSONDecodeError as e:
                print(f"Error decoding entities: {e}")

        # Convert relationships field from string to Python list
        if isinstance(item.get('relationships'), str):
            try:
                # Replace parentheses with square brackets for Python list compatibility
                relationships_str = item['relationships'].replace("(", "[").replace(")", "]")
                item['relationships'] = eval(relationships_str)  # Safely evaluate as Python list
            except Exception as e:
                print(f"Error decoding relationships: {e}")
    return data

# Process the data
parsed_data = parse_data(knowledge_graphs)

# Print the parsed data for verification
for item in parsed_data:
    print("Message:", item['message'])
    print("Entities:", item['entities'])
    print("Relationships:", item['relationships'])
    print()