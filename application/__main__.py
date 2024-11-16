

from openai import OpenAI
import openai
import os

openai.api_key = "INSERT API KEY HERE"
client = OpenAI(api_key=openai.api_key)

class LanguageToGraph:
    def __init__(self, model="gpt-4o-mini", api_key=None):
        self.model = model
        if api_key:
            openai.api_key = api_key

        self.entity_prompt = (
            "Finn kjerneentitetene relatert til eksempelvis: lokasjoner, hendelser, kjøretøy, og mennesker fra følgende tekst. "
            "Husk at det ikke er sikkert at samme datasett blir brukt og at du må ta hensyn til endret data. "
            "Ikke inkluder tvetydigheter. Hold entiteter enkle og ikke for komplekse."
        )
        self.relationship_prompt = (
            "Bruk meldingen og identifiserte entiteter. Deretter, avgjør relasjonen dem i mellom. "
            "Formater hver enkel relasjon som tripler/ontologier på formen (Subjekt, Predikat, Objekt)."
            "Husk at predikater skal ha underscore mellom seg. "
        )




    def load_msg(self, filename):
        messages = []
        if filename.endswith(".txt"):
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read().split("\n")
                for line in content:
                    if line.strip():
                        messages.append(line.strip())
        
        if "trafikktekster" not in filename:
            self.entity_prompt = self.revise_entity_prompt(messages)
            self.relationship_prompt = self.revise_entity_prompt(messages)

        return messages


    def revise_entity_prompt(self, messages):
      
        sample_messages = messages[:10]
        
        self.entity_prompt = (
            "Analyser de følgende meldingene og finn kjerneentitetene relatert til lokasjoner, hendelser, kjøretøy, og personer:\n\n"
            f"Meldinger: {', '.join(sample_messages)}\n\n"
            "Tenk på hvordan entitetene vanligvis beskrives i disse meldingene, og spesifiser dem i kategoriene:\n"
            "Lokasjon, Hendelse, Kjøretøy, og Person/Organisasjon."
        )
        
    def revise_relationship_prompt(self, messages):
     
        sample_messages = messages[:10]
        
        self.relationship_prompt = (
            "Analyser de følgende meldingene og avgjør relasjonene mellom entitetene i hver melding:\n\n"
            f"Meldinger: {', '.join(sample_messages)}\n\n"
            "Tenk på relasjonene i meldingen, og formater hver relasjon som (Subjekt, Predikat, Objekt)."
            "Husk at predikater defineres med småbokstaver og underscire."
        )

    def extract_entities_from_text(self, text):
       
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du er en assistent trent til å gjennomføre Named Entity Recognition-oppgaver"},
                {
                    "role": "user",
                    "content": (
                        f"{self.entity_prompt}\n\n"
                        f"Tekst:\n{text}\n\n"
                        "Output som standard entitet, eksempelvis (legg til flere entitetstyper hvis det er nødvendig):\n"
                        "Lokasjon: [liste med lokasjoner]\n"
                        "Hendelse: [liste med hendelser]\n"
                        "Kjøretøy: [liste med kjøretøy]\n"
                        "Person/Organisasjon: [liste med personer/organisasjoner]\n"
                    ),
                },
            ],
        )
        
        return completion.choices[0].message.content.strip()

    def extract_relationships_from_text(self, text, entities):
       
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du er en assistent trent til å gjennomføre Named Relation Extraction-oppgaver"},
                {
                    "role": "user",
                    "content": (
                        f"{self.relationship_prompt}\n\n"
                        f"Tekst:\n{text}\n\n"
                        f"Entiteter:\n{entities}\n\n"
                        "Output relasjoner som:\n"
                        "(Subjekt, Predikat, Objekt)"
                    ),
                },
            ],
        )
        return completion.choices[0].message.content.strip()


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
                "relationships": relationships
            }
            knowledge_graphs.append(knowledge_graph)
        
        return knowledge_graphs



ltg = LanguageToGraph(model="gpt-4", api_key=openai.api_key)
directory_path = "trafikktekster-20240814.txt"
messages = ltg.load_msg(directory_path)

testset_messages = messages[:10]
knowledge_graphs = ltg.process_messages(testset_messages)
