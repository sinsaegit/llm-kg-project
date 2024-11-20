# Nessecary imports for the project

import json

import openai
from constants import API_KEY
from openai import OpenAI
from rdflib import Graph, Literal, Namespace
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

openai.api_key = API_KEY  # NOTE: Change this API_KEY to your own as the original key is stored safely elsewhere.
client = OpenAI(api_key=openai.api_key)


class LanguageToGraph:
    def __init__(
        self, model="gpt-4o-mini", api_key=None
    ):  # API_KEY is None if no key argued. The same goes for chat-4o-mini.
        self.model = model
        if api_key:
            openai.api_key = api_key
        else:
            raise ValueError(
                "API key is required to initialize the LanguageToGraph class. Please provide a valid API_KEY."
            )
        self.graph = Graph()
        self.namespace = Namespace("http://example.org#")  # Define a namespace
        self.graph.bind("ex", self.namespace)
        self.graph_filename = None
        self.graph_url = "https://www.ldf.fi/service/rdf-grapher"

        # Standard promts that are stored in case revisions are proposed.
        self.entity_prompt = (
            "Du skal finne viktige entiteter som for eksempel: lokasjoner, hendelser, kjøretøy og mennesker med mer, fra følgende melding."
            "Forsøk å ikke bruke pronomen, men heller entitene pronomenene viser til."
            "Bare inkluder de identifsierte entitene, uten noe ekstra besvarelse."
        )
        self.relationship_prompt = (
            "Bruk meldingen og identifiserte entiteter til å avgjøre relasjoner. "
            "Formater hver enkelt relasjon som tripler/ontologier på formen (Subjekt, Predikat, Objekt)."
            "Husk at predikater skal ha underscore mellom seg. "
            "Bare inkluder de identifsierte triplene med relasjonen du fant som predikat, uten noe ekstra besvarelse."
        )

        # These are few shots examples stored as instance variables. They are stored like this in case automation is proposed
        self.few_shot_entities = """
            Input: 24b43w (Follesevegen, Askøy, 2024-08-12T05:50:23.2538153+00:00): Politiet har komme fram til staden. Materielle skadar i front av bilen. Bilberger er bestilte og på veg. Trafikken flyt greitt på staden.
            Output: {
            "ID": "24b43w",
            "Tid": "2024-08-12T05:50:23.2538153+00:00",
            "Lokasjon": "Follesevegen, Askøy",
            "Entiteter": [
                {"Entiteter": "Bilen", "Type": "Kjøretøy"},
                {"Entiteter": "Materielle skadar", "Type": "Hendelse"},
                {"Entiteter": "Bilberger", "Type": "Service"},
                {"Entiteter": "Politiet", "Type": "Organisasjon"}
            ]
            }

            Input: 24c8x7 (Fjøsanger, Bergen, 2024-08-11T08:18:25.5956991+00:00): Kl. 08:35 Melding om kjøring i trolig ruspåvirket tilstand. Kjørte bl.a. på felgen. Politiet stanset kjøretøy i sidegate til Fjøsangervegen. To personer i bilen. Begge fremstår ruset. Fører fremstilt for blodprøve på Bergen Legevakt. Sak opprettet. 
            Output: {
            "ID": "24c8x7",
            "Tid": "2024-08-11T08:18:25.5956991+00:00",
            "Location": "Fjøsanger, Bergen",
            "Entiteter": [
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
            "Tid": "2024-08-14T06:07:37.2057264+00:00",
            "Lokasjon": "Danmarksplass, Bergen",
            "Entiteter": [
                {"Entiteter": "3 biler", "Type": "Kjøretøy"},
                {"Entiteter": "Trafikkuhell", "Type": "Hendelse"},
                {"Entiteter": "Materielle skader", "Type": "Skade"},
                {"Entiteter": "Bergen sør", "Type": "Sted"},
                {"Entiteter": "Politiet", "Type": "Organisasjon"}
            ]
            }
            """
        # These are few shots examples stored as instance variables. They are stored like this in case automation is proposed
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
            {
            "Output": [
            {"Subjekt": "Hendelse", "Predikat": "har_id", "Objekt": "24b43w"},
            {"Subjekt": "Hendelse", "Predikat": "har_tid", "Objekt": "2024-08-12T05:50:23.2538153+00:00"},
            {"Subjekt": "Hendelse", "Predikat": "skjedde_på", "Objekt": "Follesevegen"},
            {"Subjekt": "Follesvegen", "Predikat": "del_av", "Objekt": "Askøy"},
            {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Politiet", "ankom", "Follesvegen"]},
            {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Materielle skadar", "på", "Bilen"]},
            {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Bilberger", "er", "bestilt"]},
            {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Trafikken", "flyter", "greit"]}
            ]}"

            

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
                {
                "Output": [
                {"Subjekt": "Hendelse", "Predikat": "har_id", "Objekt": "24c8x7"},
                {"Subjekt": "Hendelse", "Predikat": "har_tid", "Objekt": "2024-08-11T08:18:25.5956991+00:00"},
                {"Subjekt": "Hendelse", "Predikat": "skjedde_på", "Objekt": "Fjøsanger"},
                {"Subjekt": "Fjøsanger", "Predikat": "del_av", "Objekt": "Bergen"},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Politiet", "stanset", "Kjøretøy"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Kjøretøy", "stanset_i", "Sidegate"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Sidegate", "del_av", "Fjøsangervegen"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["To personer", "kjørte_på", "Felgen"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["To personer", "fremstår_som", "Ruset"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Fører", "fremstilt_for, "Blodprøve"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Fører", "del_av, "To personer"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Blodprøve", "gjennomføre_ved", "Bergen Legevakt"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Politiet", "opprettet", "Sak"]}
                ]}

                
            
            Input: [Meldinger: "24w0z5 (Danmarksplass, Bergen, 2024-08-14T06:07:37.2057264+00:00): 3 biler involvert i trafikkuhell. Kun meldt om materielle skader. Skaper køer mot Bergen sør. Politiet er på vei til stedet.",
                    Entiteter:{
                    "ID": "24w0z5",
                    "Timestamp": "2024-08-14T06:07:37.2057264+00:00",
                    "Lokasjon": "Danmarksplass, Bergen",
                    "Hendelse": "3 biler involvert i trafikkuhell. Kun meldt om materielle skader. Skaper køer mot Bergen sør. Politiet er på vei til stedet.",
                    "Entiteter":[
                        {"Entiteter": "3 biler", "Type": "Kjøretøy"},
                        {"Entiteter": "Trafikkuhell", "Type": "Hendelse"},
                        {"Entiteter": "Materielle skader", "Type": "Skade"},
                        {"Entiteter": "Bergen sør", "Type": "Sted"},
                        {"Entiteter": "Politiet", "Type": "Organisasjon"}
                    ]}

            Output:
                {
                "Output": [
                {"Subjekt": "Hendelse", "Predikat": "har_id", "Objekt": "24w0z5"},
                {"Subjekt": "Hendelse", "Predikat": "har_tid", "Objekt": "2024-08-14T06:07:37.2057264+00:00"},
                {"Subjekt": "Hendelse", "Predikat": "skjedde_på", "Objekt": "Danmarksplass, Bergen"},
                {"Subjekt": "Danmarksplass", "Predikat": "del_av", "Objekt": "Bergen"},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["3 biler", "involvert_i", "Trafikkuhell"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Trafikkuhell", "resulterte_i", "Materielle skader"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Trafikkuhell", "skaper", "køer mot Bergen sør"]},
                {"Subjekt": "Hendelse", "Predikat": "har_forløp", "Objekt": ["Politiet", "på_vei_til", "Trafikkuhell"]}
                ]}
                """

    # Loads different messages
    def load_msg(self, filename):
        messages = []
        if filename.endswith(".txt"):
            with open(filename, "r", encoding="utf-8") as file:
                content = file.read().split("\n")
                for line in content:
                    if line.strip():
                        messages.append(line.strip())

        if "trafikktekster" not in filename:
            self.entity_prompt = self.revise_Entiteter_prompt(messages)
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
                        f"Tilpass ny prompt slik at den ligner på den forrige prompten: {self.entity_prompt}\n\n"
                    ),
                },
            ],
            temperature=0.7,
        )

        # Update the Entiteter prompt with GPT response
        self.entity_prompt = completion.choices[0].message.content.strip()

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

        self.relationship_prompt = completion.choices[0].message.content.strip()

    def extract_entities_from_text(self, text):
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du er en assistent trent til å gjennomføre Named Entity Recognition-oppgaver for Knowledge Graphs basert på meldingen og tilhørende entiteter fra meldigen.\n"
                    "Du skal alltid produsere en hovedentitet som kan binde entietene. Eksempelvis er hele meldingen en hendelse.\n"
                    "Identifiser en ID-kode om det er mulig.\n"
                    "Returner en dictionary som kan parses som et JSON objekt.\n"
                    f"Her er noen few-shot eksempler på hvordan du finner entiteter: {self.few_shot_entities}\n",
                },
                {
                    "role": "user",
                    "content": (f"{self.entity_prompt}\n\n" f"Tekst:\n{text}\n\n"),
                },
            ],
            temperature=0.5,
        )
        return completion.choices[0].message.content.strip()

    def extract_relationships_from_text(self, text, entities):
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Du er en assistent trent til å gjennomføre Relation Extraction-oppgaver basert på meldingen og følgende entiteter som du mottar.\n"
                    "Du skal alltid identifisere en ID om det finnes og hele meldingen skal være indetifsert som en hendelse.\n"
                    "Returner som en liste som kan parses som et JSON objekt.\n"
                    f"Her er noen few-shot eksempler på hvordan du lager grafer: {self.few_shot_relations}"
                    "Lag sammenhengende grafer som vist i fewshot og alltid knytt ord i predikater med understrek.",
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
            temperature=0.5,
        )
        return completion.choices[0].message.content.strip()

    # This functions parses the relations columns of the knowledge graph-dictionary object in process_messages
    def parse_data(self, output):
        try:
            # If output is already a list of dictionaries, process it directly
            if isinstance(output, str) and output.strip().startswith("["):
                output = f'{{"Output": {output}}}'

            parsed_output = json.loads(output)
            output_data = parsed_output.get("Output", [])

            # Extract and process each relationship
            relationships = []
            for relation in output_data:
                s = relation.get("Subjekt", "")
                p = relation.get("Predikat", "")
                o = relation.get("Objekt", "")
                relationships.append((s, p, o))
            return relationships

        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Oops, encountered a parsing error: {e}. Output was: {output}")
            return []

    def process_object(self, obj):
        if isinstance(obj, list):
            return self.namespace["_".join(obj).replace(" ", "_")]
        elif isinstance(obj, str):
            return self.namespace[obj.replace(" ", "_")]
        return Literal(obj)

    def populate(self, knowledge_graphs, filename="ontology_output.ttl"):
        for _, relationships in knowledge_graphs:
            for subj, pred, obj in relationships:
                subj_uri = self.namespace[subj.replace(" ", "_")]
                pred_uri = self.namespace[pred.replace(" ", "_")]
                obj_uri = self.process_object(obj)
                self.graph.add((subj_uri, pred_uri, obj_uri))
        self.graph.serialize(destination=filename, format="turtle")
        self.graph_filename = filename
        print(f"Ontology saved to {filename}.")

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
                "Meldinger": message,
                "Entiteter": entities,
                "Relasjoner": relationships,
            }

            parsed_relationships = self.parse_data(knowledge_graph["Relasjoner"])
            knowledge_graphs.append((knowledge_graph, parsed_relationships))

        return knowledge_graphs

    def setup_selenium(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--start-maximized")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def view_graph(
        self,
        text_xpath="//textarea[@name='rdf']",
        visualize_xpath="//input[@type='submit' and @value='Visualize']",
    ):
        try:
            driver = self.setup_selenium()
            driver.get(self.graph_url)
            with open(self.graph_filename, "r", encoding="utf-8") as file:
                content = file.read()

            text_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, text_xpath))
            )
            text_box.clear()
            text_box.send_keys(content)

            visualize = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, visualize_xpath))
            )
            visualize.click()

            while True:
                user = str(input("Do you want quit [y/n]:\t"))
                if not user == "y" or "n":
                    str(input("Only use y or n:\n"))
                match user:
                    case "y":
                        break
                    case "n":
                        continue
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if driver:  # Ensure driver.quit() is only called if driver is initialized
                driver.quit()


# NOTE: This is how an LanguageToGraph object is created. The model and API_KEY parameters are optional,
# but you have to add API_KEY for the program to function properly. You can either directly pass your API_KEY
# as an argument or create a new file and import the API_KEY from there. The latter is recommended.
# It is also recommended to use a small subset of test data.
ltg = LanguageToGraph(model="gpt-4o-mini", api_key=openai.api_key)  # Initalizing class object
directory_path = "trafikktekster-20240814.txt"  # Adding test set
messages = ltg.load_msg(directory_path)  # Processing messages

testset_messages = messages[4:8]  # Using a small set of messages to create graphs due to scalability issues
knowledge_graphs = ltg.process_messages(testset_messages)  # Processing messages in prompt and parsing output
ltg.populate(knowledge_graphs)  # Populating graph
ltg.view_graph()

print("\n\n\n\n")
for item in knowledge_graphs:
    print(item[1], "\n\n")
