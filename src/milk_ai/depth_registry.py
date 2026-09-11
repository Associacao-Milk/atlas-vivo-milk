"""MILK IA - Depth Profiles Registry (Phase 3).

Source-grounded depth profiles for key references. Each profile is derived
from the thinker's actual published work. Fields that cannot be filled are
RESEARCH_GAP. Nothing is fabricated.

This module provides DEPTH_PROFILES dict and the loader function.
"""
from __future__ import annotations

from .depth_profile import (
    ConceptDepthProfile, DeepRelation, RelevanceManifold,
    cosmicoxes_projection_for,
)
from .provenance import CANONICAL_AUTHOR

_MILK_AUTHOR = CANONICAL_AUTHOR["idealized_by"]
_ADDENDUM = "addendum:final_relational_addendum"

RESEARCH_GAPS_REGISTRY = {
    "gap:bandeira": {
        "question": "Bandeira — confirmar nome/obra exactos no corpus MILK",
        "missing_evidence": ["identidade exacta do autor", "obra referenciada"],
        "territory": "literatura",
        "status": "open",
    },
    "gap:kharms_karml": {
        "question": "Daniel Kharms/Karml — confirmar identificacao exacta no corpus",
        "missing_evidence": ["nome correcto do autor", "obra referenciada"],
        "territory": "literatura",
        "status": "open",
    },
    "gap:bjork_corpus": {
        "question": "Bjork — confirmar se existe material sustentado no corpus",
        "missing_evidence": ["referencia no corpus", "contexto de uso"],
        "territory": "musica",
        "status": "open",
    },
}

DEPTH_PROFILES: dict[str, ConceptDepthProfile] = {}


def _dp(node_id, **kw):
    dp = ConceptDepthProfile(**kw)
    dp.cosmicoxes_projection = cosmicoxes_projection_for(kw.get("conceptual_nucleus", ""))
    DEPTH_PROFILES[node_id] = dp
    return dp


# --- Husserl ---
_dp("temporal:retention",
    source_pointer="source:husserl:phenomenology_of_internal_time_consciousness",
    source_type="PHILOSOPHY", author="Edmund Husserl",
    work="On the Phenomenology of the Consciousness of Internal Time (1893-1917)",
    epistemic_status="SOURCE",
    historical_context="Late 19th/early 20th century phenomenology, response to Brentano",
    foundational_problem="How does consciousness constitute temporal experience?",
    foundational_question="How can we perceive a melody as a whole when only the present note is given?",
    conceptual_nucleus="retention",
    extended_definition="Retention is the consciousness of the just-elapsed phase, still held in the present — NOT a recollection or episodic memory, but the immanent continuity of the present.",
    what_it_changes="Reveals that temporal experience is not a sequence of point-like nows but a structured flow with retentional and protentional horizons.",
    what_it_resists="Reduction of temporal experience to discrete moments; identification of retention with memory (reproduction).",
    what_it_is_not="NOT episodic memory; NOT recollection; NOT a representation of a past event.",
    axes={"temporality": "trailing edge of the present", "perception": "constitutive, not reproductive", "memory": "immanent, not representational"},
    conceptual_neighbors=["temporal:primal_impression", "temporal:protention", "temporal:melody_continuity"],
    misreading_risks=["Equating retention with episodic memory", "Treating it as a 'fading copy' of the past"])

_dp("temporal:protention",
    source_pointer="source:husserl:phenomenology_of_internal_time_consciousness",
    source_type="PHILOSOPHY", author="Edmund Husserl",
    work="On the Phenomenology of the Consciousness of Internal Time",
    epistemic_status="SOURCE",
    conceptual_nucleus="protention",
    extended_definition="Protention is the openness of consciousness toward the about-to-occur — a horizon of expectation that is structural, not an explicit prediction or hypothesis.",
    what_it_changes="Shows that every present moment carries an anticipatory horizon that is constitutive, not cognitive.",
    what_it_resists="Equating protention with explicit prediction or expectation of a specific content.",
    what_it_is_not="NOT prediction; NOT expectation of a specific event; NOT a hypothesis.",
    axes={"temporality": "leading edge of the present", "perception": "constitutive openness, not cognitive forecast"},
    conceptual_neighbors=["temporal:retention", "temporal:primal_impression", "temporal:expectation"],
    misreading_risks=["Equating protention with explicit prediction"])

_dp("temporal:primal_impression",
    source_pointer="source:husserl:phenomenology_of_internal_time_consciousness",
    source_type="PHILOSOPHY", author="Edmund Husserl",
    work="On the Phenomenology of the Consciousness of Internal Time",
    epistemic_status="SOURCE",
    conceptual_nucleus="primal impression",
    extended_definition="The narrowly present phase — the moment of givenness always already surrounded by retention and protention.",
    what_it_is_not="NOT a point-instant; NOT separable from its retentional/protentional horizons.",
    axes={"temporality": "the now-point that is never isolated"},
    conceptual_neighbors=["temporal:retention", "temporal:protention"])

# --- Schaeffer ---
_dp("sound:reduced_listening",
    source_pointer="source:schaeffer:traite_des_objets_musicaux",
    source_type="MUSIC_THEORY", author="Pierre Schaeffer",
    work="Traite des objets musicaux (1966)",
    epistemic_status="SOURCE",
    historical_context="Post-WWII musique concrete, Paris, GRM",
    foundational_problem="Can we listen to sound without identifying its source or meaning?",
    foundational_question="What remains when we bracket the cause and the signification of a sound?",
    conceptual_nucleus="reduced listening (ecoute reduite)",
    extended_definition="Attention to sonic qualities while bracketing source/cause and ordinary semantic function. A deliberate suspension analogous to phenomenological reduction.",
    what_it_changes="Creates the possibility of treating sound as an object of perception in itself.",
    what_it_resists="Automatic identification of sound with source; reduction of listening to signification.",
    what_it_is_not="NOT ignoring the source; NOT a deficit; it is an active bracketing.",
    axes={"sound": "sound as object, not as sign", "perception": "phenomenological bracketing", "attention": "deliberate redirection"},
    conceptual_neighbors=["sound:sound_object", "sound:acousmatic_reduction"],
    productive_antagonists=["listening:causal", "listening:semantic"],
    known_tensions=["Schaeffer reduced listening vs Schafer soundscape: object vs environment"])

# --- Chion ---
_dp("listening:causal",
    source_pointer="source:chion:audio_vision", source_type="MUSIC_THEORY",
    author="Michel Chion", work="Audio-Vision (1994)", epistemic_status="SOURCE",
    conceptual_nucleus="causal listening",
    extended_definition="Listening for the cause of a sound — identifying what produced it.",
    what_it_is_not="NOT listening to sound itself; NOT listening for meaning.",
    axes={"sound": "sound -> source inference"},
    conceptual_neighbors=["listening:semantic", "listening:reduced"])

_dp("listening:semantic",
    source_pointer="source:chion:audio_vision", source_type="MUSIC_THEORY",
    author="Michel Chion", work="Audio-Vision", epistemic_status="SOURCE",
    conceptual_nucleus="semantic listening",
    extended_definition="Listening to decode a sign, code, or language.",
    axes={"sound": "sound -> meaning", "language": "code/decoding"},
    conceptual_neighbors=["listening:causal", "listening:reduced"])

# --- Schafer ---
_dp("method:schafer",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="MUSIC_THEORY", author="R. Murray Schafer",
    work="The Soundscape (1977)", epistemic_status="SOURCE",
    historical_context="1970s acoustic ecology, World Soundscape Project",
    foundational_problem="How does the acoustic environment shape perception and culture?",
    foundational_question="What is the ecology of sound in human environments?",
    conceptual_nucleus="soundscape ecology",
    extended_definition="Study of the relationship between living beings and their acoustic environment. Key concepts: soundscape, soundmark, keynote, signal, ear cleaning, acoustic ecology.",
    what_it_changes="Shifts attention from sound-as-object to sound-as-environment.",
    what_it_resists="Isolation of sound from environment; reduction of listening to music only.",
    what_it_is_not="NOT reduced listening (Schaeffer); focused on the field, not the object.",
    axes={"sound": "soundscape as distributed field property", "territory": "acoustic environment", "perception": "ear cleaning"},
    conceptual_neighbors=["method:schaeffer", "sound:sound_object", "listening:causal"],
    known_tensions=["Schafer soundscape (field) vs Schaeffer reduced listening (object) — NOT the same operation"])

# --- Kandinsky ---
_dp("method:kandinsky",
    source_pointer="addendum:final_relational_addendum",
    source_type="ART_THEORY", author="Wassily Kandinsky",
    work="Point and Line to Plane (1926), Concerning the Spiritual in Art (1911)",
    epistemic_status="SOURCE",
    historical_context="Bauhaus period, early 20th century abstraction",
    foundational_problem="What are the inner forces of visual form?",
    foundational_question="How do point, line, and plane carry tension, direction, and inner necessity?",
    conceptual_nucleus="inner necessity / tension in form",
    extended_definition="Every visual element carries an inner force — tension, direction, weight — that is experiential, not merely geometric. The point is a position; the line is a force; both act on perception.",
    what_it_changes="Establishes that abstract form is charged with dynamic and affective content.",
    what_it_resists="Reduction of form to geometry; separation of perception from feeling.",
    what_it_is_not="NOT decorative grammar; driven by 'inner necessity'.",
    axes={"image": "point, line, plane as forces", "perception": "tension as perceptual force", "affect": "inner necessity"},
    conceptual_neighbors=["temporal:protention", "method:poesia_concreta"])

# --- Merleau-Ponty ---
_dp("method:merleau_ponty",
    source_pointer="source:merleau-ponty:phenomenology_of_perception",
    source_type="PHILOSOPHY", author="Maurice Merleau-Ponty",
    work="Phenomenology of Perception (1945), The Visible and the Invisible (1964)",
    epistemic_status="SOURCE",
    historical_context="Mid-20th century French phenomenology",
    foundational_problem="How does the body constitute perception before reflection?",
    foundational_question="What is the pre-reflexive relationship between body and world?",
    conceptual_nucleus="lived body / flesh (chair) / intertwining",
    extended_definition="Perception is not consciousness facing objects, but the encounter of a body that is itself part of the world. Reversibility: the seer and the seen are of the same flesh.",
    what_it_changes="Overcomes subject-object dualism; perception is embodied and reversible.",
    what_it_resists="Intellectualism; empiricism; dualism.",
    what_it_is_not="NOT psychology of perception; NOT naturalism; NOT dualism.",
    axes={"body": "lived body as primary", "perception": "pre-reflexive, reversible", "ontology": "flesh of the world"},
    conceptual_neighbors=["method:husserl", "method:boal", "device:corpo_performatico"])

# --- Winnicott ---
_dp("method:winnicott",
    source_pointer="source:winnicott:playing_and_reality",
    source_type="PSYCHOANALYSIS", author="D. W. Winnicott",
    work="Playing and Reality (1971)", epistemic_status="SOURCE",
    historical_context="British object-relations, mid-20th century",
    foundational_problem="How does play create a bridge between inner and outer reality?",
    foundational_question="What is the space where experience is neither hallucination nor external fact?",
    conceptual_nucleus="potential space / transitional object / playing",
    extended_definition="Between inner and outer reality there is a potential space — the space of play, creativity, and cultural experience. The transitional object inhabits this space. Playing is neither dream nor reality but a third area.",
    what_it_changes="Introduces a third area where creativity and culture emerge.",
    what_it_resists="Collapsing play into fantasy; reducing transitional object to comfort mechanism.",
    what_it_is_not="NOT fantasy; NOT external reality; it is a transitional third area.",
    axes={"play": "constitutive of culture", "body": "transitional", "ritual": "play as proto-ritual"},
    conceptual_neighbors=["method:boal", "work:dado_100lado", "clown:birth"])

# --- Boal ---
_dp("method:boal",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="THEATRE_THEORY", author="Augusto Boal",
    work="Theatre of the Oppressed (1974)", epistemic_status="SOURCE",
    historical_context="1960s-70s Brazil, post-coup, popular education",
    foundational_problem="How can theatre be a rehearsal for reality?",
    foundational_question="What happens when the spectator becomes the spect-actor?",
    conceptual_nucleus="spect-actor / forum / rehearsal of reality",
    extended_definition="Theatre where the spectator becomes a spect-actor who can intervene, test alternatives, and rehearse action. Forum theatre: a scene is replayed with audience intervention.",
    what_it_changes="Dissolves barrier between actor and spectator; theatre as tool for action.",
    what_it_resists="Aristotelian catharsis; passive spectatorship.",
    what_it_is_not="NOT agit-prop; NOT therapy; it is a rehearsal for reality.",
    axes={"body": "spect-actor intervenes", "sociality": "collective rehearsal", "transformation": "action follows rehearsal"},
    conceptual_neighbors=["method:freire", "method:winnicott", "work:falarte"])

# --- Freire ---
_dp("method:freire",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="PEDAGOGY", author="Paulo Freire",
    work="Pedagogy of the Oppressed (1968)", epistemic_status="SOURCE",
    historical_context="1960s Brazil, literacy among rural workers",
    foundational_problem="How can education be liberating rather than domesticating?",
    foundational_question="What is the relationship between reading the word and reading the world?",
    conceptual_nucleus="reading the world / dialogue / critical consciousness / praxis",
    extended_definition="Education is not deposit of information but a dialogical process where learners read the word AND the world. Praxis = reflection + action.",
    what_it_changes="Reframes literacy as political and existential.",
    what_it_resists="Banking education; separation of learning from life.",
    what_it_is_not="NOT a teaching method; NOT a literacy technique; it is pedagogy of liberation.",
    axes={"language": "reading the world precedes reading the word", "sociality": "dialogue", "territory": "reading the territory", "transformation": "praxis"},
    conceptual_neighbors=["method:boal", "device:mapping_territorial"])

# --- Deleuze ---
_dp("method:deleuze",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="PHILOSOPHY", author="Gilles Deleuze",
    work="A Thousand Plateaus (with Guattari, 1980), Difference and Repetition (1968)",
    epistemic_status="SOURCE",
    conceptual_nucleus="agencement / becoming / deterritorialization / multiplicity",
    extended_definition="Not reducible to 'rhizome'. Key concepts: agencement (assemblage), becoming (productive encounter), deterritorialization/reterritorialization, affect/intensity, map/trace.",
    what_it_changes="Replaces structural oppositions with dynamic processes.",
    what_it_resists="Binary structures; fixed identities; reduction of desire to lack.",
    what_it_is_not="NOT just 'rhizome'; NOT postmodern relativism.",
    axes={"territory": "deterritorialization/reterritorialization", "affect": "intensity, pre-personal", "transformation": "becoming"},
    conceptual_neighbors=["method:guattari", "work:cosmic_flow", "method:chaos_complexity"])

# --- Barthes ---
_dp("method:barthes",
    source_pointer="addendum:final_relational_addendum",
    source_type="LITERARY_THEORY", author="Roland Barthes",
    work="Camera Lucida (1980), The Grain of the Voice (1972), S/Z (1970)",
    epistemic_status="SOURCE",
    conceptual_nucleus="punctum / studium / writerly text / grain of the voice",
    extended_definition="Not reducible to punctum. Studium = general cultural interest; punctum = the detail that wounds. Writerly text invites participation. Grain of the voice: body in language.",
    what_it_changes="Introduces the wound (punctum) as distinct from cultural competence (studium).",
    what_it_resists="Reduction of reading to decoding; dissolution of body in text.",
    what_it_is_not="NOT just punctum; includes body, grain, and the neutral.",
    axes={"image": "punctum vs studium", "language": "writerly vs readerly", "sound": "grain of voice — body in language", "affect": "punctum as wound"},
    conceptual_neighbors=["method:didi_huberman", "work:palavra_ritual", "method:bakhtin"])

# --- Llansol ---
_dp("method:llansol",
    source_pointer="addendum:final_relational_addendum",
    source_type="LITERATURE", author="Maria Gabriela Llansol",
    work="Os Pecados (1979+), Cidade de Lisboa", epistemic_status="SOURCE",
    conceptual_nucleus="cena-fulgor / legencia / encontro do diverso / geografia textual",
    extended_definition="Not reducible to 'fragment'. Cena-fulgor: sudden condensation where diverse elements meet. Legencia: writing-governing as attention to emerging relations. Geografia textual: text as map, not narrative. Sobreimpressao: layering of times and spaces. Leitura-escrita: reading and writing as one act.",
    what_it_changes="Replaces narrative with encounter; text is a geography of meetings.",
    what_it_resists="Linear narrative; causal explanation; reduction of writing to representation.",
    what_it_is_not="NOT 'fragment'; NOT 'stream of consciousness'; it is a geography of encounters.",
    axes={"language": "leitura-escrita, sobreimpressao", "territory": "geografia textual", "temporality": "sobreimpressao de tempos", "image": "cena-fulgor"},
    conceptual_neighbors=["method:didi_huberman", "method:barthes", "work:palavra_ritual"])

# --- Didi-Huberman ---
_dp("method:didi_huberman",
    source_pointer="addendum:final_relational_addendum",
    source_type="ART_HISTORY", author="Georges Didi-Huberman",
    work="Survivance des images (2002), Devant l'image (1990)", epistemic_status="SOURCE",
    conceptual_nucleus="Nachleben / Pathosformel / anachronism / montage",
    extended_definition="Images survive (Nachleben), return across centuries, carrying pathos (Pathosformel). Anachronism is not error but condition. Montage of anachronistic images produces knowledge.",
    what_it_changes="Introduces anachronism as productive for art history.",
    what_it_resists="Linear art history; images belonging to their period only.",
    what_it_is_not="NOT relativism; NOT anti-history; it is a theory of survival across time.",
    axes={"image": "Nachleben — survival", "temporality": "anachronism as condition", "affect": "Pathosformel — persisting formula of affect", "memory": "survival, not recollection"},
    conceptual_neighbors=["method:llansol", "method:barthes", "method:wabi_sabi"])

# --- Camus ---
_dp("method:camus",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="PHILOSOPHY", author="Albert Camus",
    work="The Myth of Sisyphus (1942), The Rebel (1951)", epistemic_status="SOURCE",
    conceptual_nucleus="absurd / lucidity / revolt / measure",
    extended_definition="The absurd is not chaos — it is the confrontation between human need for meaning and the silence of the world. Lucidity: seeing the absurd clearly. Revolt: not surrendering. Measure: Mediterranean virtue of limit.",
    what_it_changes="Reframes absurd as starting point for lucidity and revolt.",
    what_it_resists="Nihilism; suicide; reduction of absurd to meaninglessness.",
    what_it_is_not="NOT nihilism; NOT existentialism (Camus rejected the label).",
    axes={"ontology": "absurd as relationship", "affect": "lucidity, not despair", "transformation": "revolt as lucid action"},
    conceptual_neighbors=["method:beckett", "method:ionesco", "clown:birth"])

# --- Artaud ---
_dp("method:artaud",
    source_pointer="addendum:final_relational_addendum",
    source_type="THEATRE_THEORY", author="Antonin Artaud",
    work="The Theatre and Its Double (1938)", epistemic_status="SOURCE",
    conceptual_nucleus="cruelty / presence / body / theatre of cruelty",
    extended_definition="Not reducible to 'shock'. Cruelty is not violence but exposure to necessity. Theatre acts on the nervous system, not the intellect. Presence: body as event, not representation.",
    what_it_changes="Replaces representation with exposure; theatre as bodily event.",
    what_it_resists="Literary theatre; representation; reduction of cruelty to violence.",
    what_it_is_not="NOT shock; NOT violence; it is exposure to necessity.",
    axes={"body": "body as event", "performance": "presence, not representation", "affect": "cruelty as exposure", "ritual": "theatre as ritual exposure"},
    conceptual_neighbors=["method:boal", "method:camus", "clown:birth"])

# --- Bakhtin ---
_dp("method:bakhtin",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="LITERARY_THEORY", author="Mikhail Bakhtin",
    work="The Dialogic Imagination (1975), Rabelais and His World (1965)", epistemic_status="SOURCE",
    conceptual_nucleus="dialogism / heteroglossia / carnivalization / chronotope",
    extended_definition="Dialogism: every utterance is addressed and responds. Heteroglossia: language is stratified into social voices. Carnivalization: temporary inversion of hierarchies. Chronotope: time-space configuration in genre.",
    what_it_changes="Shows language is never unitary; narrative is always dialogical.",
    what_it_resists="Monologism; idea of single neutral language; formalism without social context.",
    what_it_is_not="NOT relativism; NOT mere multiplicity; it is structured dialogue of differences.",
    axes={"language": "dialogism, heteroglossia", "sociality": "carnival", "territory": "chronotope", "ritual": "carnival as proto-ritual"},
    conceptual_neighbors=["method:barthes", "method:foucault", "work:palavra_ritual"])

# --- Foucault ---
_dp("method:foucault",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="PHILOSOPHY", author="Michel Foucault",
    work="The Archaeology of Knowledge (1969), Discipline and Punish (1975)", epistemic_status="SOURCE",
    conceptual_nucleus="dispositif / power-knowledge / genealogy / normalization",
    extended_definition="Not reducible to 'power'. Dispositif: heterogeneous ensemble of discourses, institutions, practices. Power-knowledge: mutually constitutive. Genealogy: historical emergence. Normalization: production of norms.",
    what_it_changes="Reframes power as productive (not merely repressive).",
    what_it_resists="Reduction of everything to power; idea of neutral knowledge; sovereign power.",
    what_it_is_not="NOT 'everything is power'; NOT relativism.",
    axes={"power": "power-knowledge as productive", "sociality": "normalization", "language": "discourse as practice"},
    conceptual_neighbors=["method:bakhtin", "method:bourdieu", "zine:identity_revisable"])

# --- Bourdieu ---
_dp("method:bourdieu",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="SOCIOLOGY", author="Pierre Bourdieu",
    work="Distinction (1979), The Logic of Practice (1990)", epistemic_status="SOURCE",
    conceptual_nucleus="field / habitus / capital / position / distinction",
    extended_definition="Field: structured social space. Habitus: embodied dispositions. Capital: economic, cultural, social, symbolic. Symbolic violence: imposition of cultural categories as legitimate.",
    what_it_changes="Shows taste is socially structured; practice is neither conscious choice nor determinism.",
    what_it_resists="Pure rational choice; pure determinism; naturalization of taste.",
    what_it_is_not="NOT economic determinism; NOT rational choice.",
    axes={"sociality": "field, position", "body": "habitus — embodied dispositions", "power": "symbolic violence"},
    conceptual_neighbors=["method:foucault", "method:bakhtin"])

# --- Maturana/Varela ---
_dp("method:maturana_varela",
    source_pointer="addendum:final_relational_addendum",
    source_type="BIOLOGY_PHILOSOPHY", author="Humberto Maturana, Francisco Varela",
    work="The Tree of Knowledge (1987), Autopoiesis and Cognition (1980)", epistemic_status="SOURCE",
    conceptual_nucleus="autopoiesis / structural coupling / enaction",
    extended_definition="Autopoiesis: self-producing system. Structural coupling: recurrent interaction producing mutual perturbations. Enaction (Varela/Thompson/Rosch 1991): cognition is enacted, not representational. Provenance: enaction is specifically from Varela/Thompson/Rosch 1991, not from Maturana/Varela 1980.",
    what_it_changes="Reframes cognition as constitutive, not representative.",
    what_it_resists="Representationalism; computer metaphor; pre-given world.",
    what_it_is_not="NOT representation; NOT computation.",
    axes={"ontology": "autopoiesis", "perception": "enaction", "body": "living body as cognitive"},
    conceptual_neighbors=["method:merleau_ponty", "method:deleuze"],
    misreading_risks=["Equating enaction with autopoiesis (enaction is later development)"])

# --- Bispo do Rosario ---
_dp("method:bispo_do_rosario",
    source_pointer="addendum:final_relational_addendum",
    source_type="ART", author="Arthur Bispo do Rosario",
    work="Inventario do universo (c. 1938-1989)", epistemic_status="SOURCE",
    conceptual_nucleus="inventory / rearrangement / naming / materiality / singular archive",
    extended_definition="Inventory of the universe from found materials — textiles, wood, metal, thread. Named and classified by his own system. Resists pathologization and romanticization. The archive is singular: neither collection nor institutional art.",
    what_it_changes="Shows archive can be constituted from discarded materials through naming.",
    what_it_resists="Pathologization; romanticization; institutional classification; museum as only frame.",
    what_it_is_not="NOT 'outsider art' as exotic; NOT art-brut as symptom; it is a singular inventory.",
    axes={"materiality": "discarded materials as archive", "territory": "naming as territorialization", "memory": "singular memory of the world"},
    conceptual_neighbors=["method:wabi_sabi", "method:foucault", "work:dado_100lado"],
    misreading_risks=["Pathologizing; romanticizing as 'mad genius'"])

# --- Clown birth ---
_dp("clown:birth",
    source_pointer="addendum:final_relational_addendum",
    source_type="PERFORMANCE_STUDIES", author=_MILK_AUTHOR,
    work="N/A (MILK curatorial study)", epistemic_status="METHOD_TRANSLATION",
    conceptual_nucleus="birth / failure / exposure / vulnerability / presence / response / transformation",
    extended_definition="Not reducible to humor or laughter. The clown is born when a person fails in front of others, exposes vulnerability, and the failure is transformed into play. Requires: exposure, vulnerability, presence, response, transformation.",
    what_it_changes="Reframes failure as constitutive of presence.",
    what_it_resists="Reduction to humor; idea that failure must be corrected; separation of performer from audience.",
    what_it_is_not="NOT humor; NOT laughter; NOT comedy; it is the birth of presence from failure.",
    axes={"body": "failure as bodily exposure", "play": "failure -> play", "affect": "vulnerability and presence", "transformation": "failure -> encounter -> new possibility"},
    conceptual_neighbors=["method:winnicott", "method:camus", "method:artaud", "method:boal"])

# --- DOPAFANIA ---
_dp("milk:dopafania",
    source_pointer=_ADDENDUM, source_type="AUTHORIAL_CONCEPT",
    author=_MILK_AUTHOR, work="N/A", epistemic_status="EXPERIMENTAL_HYPOTHESIS",
    conceptual_nucleus="expectation -> interruption -> recognition -> sudden salience -> epiphany",
    extended_definition="NOT dopamine, NOT mechanism, NOT diagnosis. Experiential structure: expectation meets unexpected relation, recognition occurs, sudden subjective salience. Neuroscience bridge remains SEPARATE.",
    what_it_is_not="NOT dopamine; NOT a mechanism; NOT a diagnosis; NOT a scientific fact.",
    axes={"affect": "sudden salience", "temporality": "expectation -> interruption", "transformation": "recognition -> revaluation"},
    conceptual_neighbors=["temporal:protention", "temporal:surprise", "neuro:reward_prediction_error"],
    misreading_risks=["Treating as neuroscientific fact; equating with dopamine"],
    human_validation_required=True)

# --- ESCUTA_IDENTITARIA ---
_dp("milk:escuta_identitaria",
    source_pointer=_ADDENDUM, source_type="AUTHORIAL_CONCEPT",
    author=_MILK_AUTHOR, work="N/A", epistemic_status="METHOD_TRANSLATION",
    conceptual_nucleus="sound/voice/word -> autobiographical/territorial resonance -> identity trace",
    extended_definition="Authorial MILK method extension, not a Schaeffer category. Sound triggers autobiographical or territorial resonance. Identity trace is relational, revisable, situated. Does not infer fixed identity.",
    what_it_is_not="NOT a Schaeffer category; NOT a psychological profile; NOT a fixed identity.",
    axes={"sound": "listening carries identity", "memory": "autobiographical resonance", "territory": "territorial resonance", "affect": "recognition, not cognition"},
    conceptual_neighbors=["sound:reduced_listening", "method:schafer", "listening:causal", "method:oral_traditions"])

# --- PALAVRA_RITUAL ---
_dp("work:palavra_ritual",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="AUTHORIAL_WORK", author=_MILK_AUTHOR,
    work="Palavra Ritual", epistemic_status="SOURCE",
    conceptual_nucleus="word / ritual / performance / voice",
    extended_definition="The word becomes ritual — not text-as-meaning but word-as-body, word-as-event. Spoken, not merely written; performed, not merely communicated.",
    axes={"language": "word as body before meaning", "voice": "spoken word as ritual", "performance": "word as event", "ritual": "speaking as proto-ritual"},
    conceptual_neighbors=["listening:semantic", "milk:escuta_identitaria", "method:bakhtin", "method:barthes"])

# --- Campo do Possivel ---
_dp("work:campo_do_possivel",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="AUTHORIAL_WORK", author=_MILK_AUTHOR,
    work="CAMPO DO POSSIVEL", epistemic_status="SOURCE",
    conceptual_nucleus="possibility / encounter / infrastructure",
    extended_definition="Infrastructure of encounter — space where possibility is not predetermined but emerges from interaction of bodies, words, materials.",
    axes={"space": "potential space for encounter", "play": "possibility without predetermined outcome", "transformation": "possibility as emergent"},
    conceptual_neighbors=["method:winnicott", "method:boal", "work:dado_100lado"])

# --- Dado sem lado ---
_dp("work:dado_sem_lado",
    source_pointer="biblioteca/milk_framework_conceptual.json",
    source_type="AUTHORIAL_WORK", author=_MILK_AUTHOR,
    work="CUBO / Dado sem lado", epistemic_status="SOURCE",
    conceptual_nucleus="dice without sides / generative indeterminacy / open form",
    extended_definition="A dice with no fixed faces — generative device that opens a space of possibility. Related to DADO 100LADO but conceptually distinct.",
    axes={"play": "indeterminate play", "transformation": "outcome not predetermined", "uncertainty": "the dice that cannot settle"},
    conceptual_neighbors=["work:dado_100lado", "method:winnicott", "method:chaos_complexity"])
