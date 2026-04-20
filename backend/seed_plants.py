# ============================================================
# SCRIPT : seed_plants.py
# RÔLE   : Insérer les plantes de Côte d'Ivoire en base
# USAGE  : python seed_plants.py
# ============================================================

import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from database import SessionLocal, engine, Base
from models import Plant

Base.metadata.create_all(bind=engine)

PLANTS = [
    # ── PLANTES ALIMENTAIRES ──────────────────────────────────
    dict(
        name="Manioc", local_name="Attiéké (Dida)", scientific_name="Manihot esculenta",
        family="Euphorbiaceae",
        description="Arbuste tropical dont les racines tubéreuses constituent l'aliment de base en Côte d'Ivoire. Source principale de glucides pour des millions de personnes.",
        habitat="Zones tropicales humides, jardins, champs cultivés",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=True, is_medicinal=True, is_invasive=False,
        toxicity_level="faible",
        culinary_uses="Attiéké (semoule fermentée), foutou, placali, farine, tapioca. Les feuilles se consomment cuites comme légume.",
        medicinal_uses="Feuilles utilisées contre la fièvre et l'hypertension. Cataplasme de feuilles contre les maux de tête."
    ),
    dict(
        name="Igname", local_name="Yam (Baoulé)", scientific_name="Dioscorea rotundata",
        family="Dioscoreaceae",
        description="Tubercule sacré en Côte d'Ivoire, célébrée par la Fête de l'Igname. Plante grimpante aux tubercules riches en amidon.",
        habitat="Savanes, forêts claires, zones cultivées",
        regions="Centre, Nord, Ouest (Bouaké, Korhogo, Man)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Foutou d'igname, igname pilée, igname bouillie, chips d'igname, igname grillée au feu.",
        medicinal_uses="Régulation de la glycémie, source de dioscorine aux propriétés anti-inflammatoires."
    ),
    dict(
        name="Plantain", local_name="Aloco / Alloco", scientific_name="Musa paradisiaca",
        family="Musaceae",
        description="Bananier à fruits amylacés, indissociable de la cuisine ivoirienne. L'alloco (plantain frit) est le snack national.",
        habitat="Zones humides, jardins, plantations",
        regions="Sud, Centre, Ouest (Abidjan, San-Pédro, Man)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Alloco (frit), plantain bouilli, kedjenu, foufou. Feuilles utilisées comme emballage alimentaire.",
        medicinal_uses="Traitement de la diarrhée, cicatrisation des plaies, régulation de la tension artérielle."
    ),
    dict(
        name="Gombo", local_name="Gnangnan / Kanjà", scientific_name="Abelmoschus esculentus",
        family="Malvaceae",
        description="Plante potagère aux fruits mucilagineuses très utilisés dans les sauces ivoiriennes. Riche en fibres et vitamines.",
        habitat="Jardins potagers, champs",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Sauce gombo, soupe de gombo, gombo séché en poudre comme épaississant.",
        medicinal_uses="Régulation du cholestérol, traitement du diabète, anti-inflammatoire, soulagement des maux d'estomac."
    ),
    dict(
        name="Aubergine africaine", local_name="Djakato / Djèkpa", scientific_name="Solanum macrocarpon",
        family="Solanaceae",
        description="Aubergine locale à grand fruit vert ou violet, distincte de l'aubergine européenne. Très présente dans les marchés ivoiriens.",
        habitat="Jardins, marchés, zones cultivées",
        regions="Sud et Centre Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Sauce aubergine, grillée, en ragoût avec poisson ou viande.",
        medicinal_uses="Anti-inflammatoire, régulation de la glycémie, propriétés antioxydantes."
    ),
    dict(
        name="Feuille de patate douce", local_name="Patate douce", scientific_name="Ipomoea batatas",
        family="Convolvulaceae",
        description="Plante rampante dont les tubercules et les feuilles sont comestibles. Très cultivée pour son rendement et sa valeur nutritive.",
        habitat="Champs cultivés, jardins",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Tubercules bouillis, frits ou rôtis. Feuilles consommées comme légume vert.",
        medicinal_uses="Riche en bêta-carotène, antioxydant, régulation de la glycémie."
    ),
    dict(
        name="Morelle noire", local_name="Gnégné / N'drowa", scientific_name="Solanum nigrum",
        family="Solanaceae",
        description="Petite plante herbacée aux baies noires très consommées en Côte d'Ivoire comme légume feuille. Attention : les baies crues sont légèrement toxiques.",
        habitat="Bords de chemins, jardins, zones rudérales",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=True, is_medicinal=True, is_invasive=False,
        toxicity_level="faible",
        culinary_uses="Feuilles cuites en sauce (cuisson détruit les alcaloïdes). Base de la sauce gnégné.",
        medicinal_uses="Antipyrétique, anti-inflammatoire, traitement des affections cutanées."
    ),
    dict(
        name="Piment", local_name="Kpimi / Poivre de Cayenne", scientific_name="Capsicum frutescens",
        family="Solanaceae",
        description="Arbuste aux fruits très piquants, incontournable de la cuisine ivoirienne. Riche en capsaïcine.",
        habitat="Jardins, marchés",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Condiment universel, sauces pimentées, marinades, piment séché en poudre.",
        medicinal_uses="Analgésique local, stimulant digestif, antimicrobien, traitement des douleurs articulaires."
    ),

    # ── PLANTES MÉDICINALES ───────────────────────────────────
    dict(
        name="Neem", local_name="Nim / Lilas des Indes", scientific_name="Azadirachta indica",
        family="Meliaceae",
        description="Arbre aux propriétés médicinales exceptionnelles, surnommé 'pharmacie du village' en Afrique. Introduit en Côte d'Ivoire, maintenant très répandu.",
        habitat="Zones urbaines, villages, savanes",
        regions="Nord et Centre (Korhogo, Bouaké)",
        is_edible=False, is_toxic=True, is_medicinal=True, is_invasive=True,
        toxicity_level="moyen",
        culinary_uses="Non consommé en alimentation courante.",
        medicinal_uses="Antipaludéen, antibactérien, antifongique. Décoction de feuilles contre le paludisme, la fièvre, les infections cutanées. Huile de neem anti-parasitaire."
    ),
    dict(
        name="Citronnelle", local_name="Verveine des Indes", scientific_name="Cymbopogon citratus",
        family="Poaceae",
        description="Graminée aromatique à l'odeur citronnée intense. Cultivée comme plante médicinale et aromatique dans tout le pays.",
        habitat="Jardins, abords de maisons",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Infusion (tisane), aromatisation de plats, marinades de poisson.",
        medicinal_uses="Antistress, sédatif léger, traitement des maux d'estomac, répulsif naturel contre les moustiques, fièvre."
    ),
    dict(
        name="Moringa", local_name="Arbre miracle / Ben ailé", scientific_name="Moringa oleifera",
        family="Moringaceae",
        description="Surnommé 'arbre miracle', ses feuilles sont parmi les aliments les plus nutritifs au monde. Très cultivé dans le Nord ivoirien.",
        habitat="Zones sèches, jardins, abords de villages",
        regions="Nord (Korhogo, Ferkessédougou, Odienné)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Feuilles en sauce, poudre de feuilles comme complément nutritionnel, graines consommées comme noix.",
        medicinal_uses="Antioxydant puissant, anti-inflammatoire, régulation de la glycémie et du cholestérol, traitement de la malnutrition."
    ),
    dict(
        name="Vernonia", local_name="Ewuro / Kponan", scientific_name="Vernonia amygdalina",
        family="Asteraceae",
        description="Arbuste aux feuilles amères très utilisées en médecine traditionnelle ivoirienne. Appelé 'feuille amère'.",
        habitat="Forêts secondaires, jardins, villages",
        regions="Sud et Ouest (Abidjan, San-Pédro, Man)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Feuilles cuites comme légume (amertume réduite par cuisson), soupe de feuilles amères.",
        medicinal_uses="Antipaludéen, antidiabétique, traitement des infections intestinales, stimulation de l'appétit, détoxification du foie."
    ),
    dict(
        name="Papayer", local_name="Papaye / Brofwé", scientific_name="Carica papaya",
        family="Caricaceae",
        description="Arbre fruitier tropical aux multiples usages médicinaux et alimentaires. Présent dans tous les jardins ivoiriens.",
        habitat="Jardins, plantations, zones tropicales",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Fruit mûr en dessert, papaye verte en salade ou sauce, graines comme condiment poivré.",
        medicinal_uses="Papaïne (enzyme digestive), traitement du paludisme avec les feuilles, antiparasitaire, cicatrisant."
    ),
    dict(
        name="Gingembre", local_name="Gingembre sauvage", scientific_name="Zingiber officinale",
        family="Zingiberaceae",
        description="Rhizome aromatique et médicinal cultivé et sauvage, très populaire dans la médecine traditionnelle et la cuisine.",
        habitat="Jardins, zones humides",
        regions="Sud et Ouest",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Boisson gingembre (très populaire), épice dans les plats, décoction.",
        medicinal_uses="Anti-nauséeux, anti-inflammatoire, traitement du rhume et de la toux, stimulant circulatoire."
    ),
    dict(
        name="Aloe vera", local_name="Aloès", scientific_name="Aloe vera",
        family="Asphodelaceae",
        description="Plante succulente aux feuilles charnues remplies d'un gel aux propriétés thérapeutiques reconnues.",
        habitat="Zones sèches, jardins",
        regions="Nord et Centre",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Gel ajouté aux boissons, jus d'aloès.",
        medicinal_uses="Cicatrisant des brûlures, traitement des coups de soleil, hydratation cutanée, laxatif doux."
    ),
    dict(
        name="Basilic africain", local_name="Efirin / Kébé-kébé", scientific_name="Ocimum gratissimum",
        family="Lamiaceae",
        description="Basilic sauvage africain à l'odeur camphrée, différent du basilic méditerranéen. Très utilisé en médecine traditionnelle.",
        habitat="Jardins, zones rudérales, forêts secondaires",
        regions="Toute la Côte d'Ivoire",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Condiment aromatique dans les sauces et soupes.",
        medicinal_uses="Antibactérien, antifongique, traitement de la toux, fièvre, infections respiratoires et digestives."
    ),
    dict(
        name="Ricin", local_name="Palma Christi", scientific_name="Ricinus communis",
        family="Euphorbiaceae",
        description="Grande plante aux feuilles palmées très reconnaissables. Ses graines contiennent de la ricine, l'une des substances les plus toxiques connues.",
        habitat="Bords de routes, zones perturbées",
        regions="Toute la Côte d'Ivoire",
        is_edible=False, is_toxic=True, is_medicinal=True, is_invasive=True,
        toxicity_level="élevé",
        culinary_uses="NON COMESTIBLE. L'huile purifiée (huile de ricin) est uniquement à usage externe.",
        medicinal_uses="Huile de ricin (usage externe) : laxatif puissant, soin des cheveux et de la peau. ATTENTION : graines mortelles."
    ),

    # ── ARBRES EMBLÉMATIQUES ──────────────────────────────────
    dict(
        name="Karité", local_name="Sii (Dioula)", scientific_name="Vitellaria paradoxa",
        family="Sapotaceae",
        description="Arbre sacré des savanes africaines. Son beurre est utilisé en cuisine, cosmétique et médecine. Symbole du Nord ivoirien.",
        habitat="Savanes soudaniennes",
        regions="Nord (Korhogo, Boundiali, Odienné, Ferkessédougou)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Beurre de karité pour la cuisine, amandes grillées consommées.",
        medicinal_uses="Beurre de karité : cicatrisant, anti-inflammatoire, hydratant, protection solaire naturelle."
    ),
    dict(
        name="Baobab", local_name="Bohi (Dioula)", scientific_name="Adansonia digitata",
        family="Malvaceae",
        description="Géant des savanes africaines pouvant vivre plusieurs millénaires. Toutes ses parties sont utilisées : fruit, feuilles, écorce.",
        habitat="Savanes sèches",
        regions="Nord (Korhogo, Ferkessédougou)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Pulpe du fruit (pain de singe) en boisson, feuilles séchées en sauce (lalo), graines en condiment.",
        medicinal_uses="Antipyrétique, traitement de la diarrhée, riche en vitamine C, calcium et antioxydants."
    ),
    dict(
        name="Palmier à huile", local_name="Palmier d'Afrique", scientific_name="Elaeis guineensis",
        family="Arecaceae",
        description="Principale culture de rente de Côte d'Ivoire avec le cacao et le café. Source d'huile de palme et de vin de palme.",
        habitat="Forêts humides, plantations",
        regions="Sud et Ouest (Abidjan, San-Pédro, Sassandra)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Huile de palme rouge pour la cuisine, vin de palme (sodabi), noix de palme dans les sauces.",
        medicinal_uses="Huile rouge riche en bêta-carotène et vitamine E, traitement de la malnutrition."
    ),
    dict(
        name="Kapokier", local_name="Fromager / Arbre à coton", scientific_name="Ceiba pentandra",
        family="Malvaceae",
        description="Arbre géant pouvant dépasser 60m, souvent sacré dans les villages ivoiriens. Fournit le kapok utilisé comme rembourrage.",
        habitat="Forêts tropicales, villages",
        regions="Sud et Centre",
        is_edible=False, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Graines et feuilles parfois consommées dans certaines régions.",
        medicinal_uses="Écorce utilisée contre la fièvre, le paludisme et les douleurs rhumatismales."
    ),
    dict(
        name="Rônier", local_name="Ronier / Palmier rônier", scientific_name="Borassus aethiopum",
        family="Arecaceae",
        description="Grand palmier des savanes du Nord, emblème du paysage soudanais ivoirien. Plante multi-usages.",
        habitat="Savanes, bords de marigots",
        regions="Nord (Korhogo, Boundiali)",
        is_edible=True, is_toxic=False, is_medicinal=False, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Pulpe des jeunes fruits consommée, sève fermentée en vin de rônier, cœur du palmier (chou palmiste).",
        medicinal_uses="Sève utilisée comme boisson tonique et reconstructive."
    ),
    dict(
        name="Acacia", local_name="Épineux / Gonakier", scientific_name="Acacia senegal",
        family="Fabaceae",
        description="Arbuste épineux des zones sèches, source de gomme arabique. Très résistant à la sécheresse.",
        habitat="Savanes sèches, zones dégradées",
        regions="Extrême Nord",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Gomme arabique comme additif alimentaire et épaississant.",
        medicinal_uses="Gomme arabique : protecteur des muqueuses digestives, traitement de la toux."
    ),

    # ── PLANTES TOXIQUES / DANGEREUSES ───────────────────────
    dict(
        name="Datura", local_name="Herbe du diable / Pomme épineuse", scientific_name="Datura stramonium",
        family="Solanaceae",
        description="Plante très toxique aux grandes fleurs blanches en trompette. Toutes ses parties contiennent des alcaloïdes dangereux.",
        habitat="Bords de routes, zones perturbées, villages",
        regions="Centre et Nord",
        is_edible=False, is_toxic=True, is_medicinal=False, is_invasive=True,
        toxicity_level="élevé",
        culinary_uses="STRICTEMENT NON COMESTIBLE. Dangereusement toxique.",
        medicinal_uses="Usage traditionnel très risqué. Alcaloïdes (scopolamine, atropine) utilisés uniquement en médecine moderne sous contrôle strict."
    ),
    dict(
        name="Euphorbe", local_name="Euphorbe candelabra", scientific_name="Euphorbia tirucalli",
        family="Euphorbiaceae",
        description="Arbuste succulent en forme de cierge. Son latex blanc est extrêmement irritant et cancérigène.",
        habitat="Haies, zones sèches",
        regions="Nord et Centre",
        is_edible=False, is_toxic=True, is_medicinal=False, is_invasive=False,
        toxicity_level="élevé",
        culinary_uses="NON COMESTIBLE. Latex dangereux pour les yeux et la peau.",
        medicinal_uses="Utilisé avec extrême précaution en médecine traditionnelle contre les verrues."
    ),
    dict(
        name="Jatropha", local_name="Pourghère / Médicinier", scientific_name="Jatropha curcas",
        family="Euphorbiaceae",
        description="Arbuste aux graines très toxiques mais utilisé comme clôture vivante. Ses graines produisent un biocarburant.",
        habitat="Haies, zones dégradées",
        regions="Toute la Côte d'Ivoire",
        is_edible=False, is_toxic=True, is_medicinal=True, is_invasive=False,
        toxicity_level="élevé",
        culinary_uses="NON COMESTIBLE. Les graines sont toxiques.",
        medicinal_uses="Latex cicatrisant, huile purifiée laxative puissante. Usage traditionnel contre les parasites cutanés."
    ),

    # ── PLANTES AQUATIQUES / ENVAHISSANTES ───────────────────
    dict(
        name="Jacinthe d'eau", local_name="Herbe flottante", scientific_name="Eichhornia crassipes",
        family="Pontederiaceae",
        description="Plante aquatique envahissante aux fleurs violettes. Colonise les lagunes et cours d'eau, perturbant l'écosystème.",
        habitat="Lagunes, rivières, lacs",
        regions="Lagune Ébrié (Abidjan), fleuves du Sud",
        is_edible=True, is_toxic=False, is_medicinal=False, is_invasive=True,
        toxicity_level="aucun",
        culinary_uses="Feuilles et pétioles consommables après cuisson dans certaines régions.",
        medicinal_uses="Peu d'usages médicinaux documentés."
    ),
    dict(
        name="Laitue d'eau", local_name="Pistia", scientific_name="Pistia stratiotes",
        family="Araceae",
        description="Plante aquatique flottante envahissante formant des tapis denses sur les plans d'eau.",
        habitat="Lagunes, mares, cours d'eau lents",
        regions="Sud (lagunes côtières)",
        is_edible=False, is_toxic=False, is_medicinal=True, is_invasive=True,
        toxicity_level="aucun",
        culinary_uses="Non comestible directement.",
        medicinal_uses="Utilisée en médecine traditionnelle contre les affections cutanées et les hémorroïdes."
    ),

    # ── PLANTES AROMATIQUES ET ÉPICES ────────────────────────
    dict(
        name="Poivre de Guinée", local_name="Poivre selim / Kani", scientific_name="Xylopia aethiopica",
        family="Annonaceae",
        description="Épice africaine aux fruits allongés très aromatiques. Incontournable de la cuisine et de la médecine traditionnelle ivoirienne.",
        habitat="Forêts humides secondaires",
        regions="Forêts du Sud et de l'Ouest",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Épice dans les soupes, marinades, boissons (gnimini). Goût poivré-aromatique unique.",
        medicinal_uses="Stimulant, carminatif, traitement des infections bronchiques, post-partum en médecine traditionnelle."
    ),
    dict(
        name="Noix de kola", local_name="Ora / Wolo (Dioula)", scientific_name="Cola nitida",
        family="Malvaceae",
        description="Arbre de la forêt dense ivoirienne. Sa noix est symbole d'hospitalité et utilisée comme stimulant. Contient de la caféine.",
        habitat="Forêts humides denses",
        regions="Ouest et Sud-Ouest (Man, San-Pédro)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Noix mâchées comme stimulant, offrande lors de cérémonies.",
        medicinal_uses="Stimulant (caféine), coupe-faim, traitement des maux de tête, aphrodisiaque traditionnel."
    ),
    dict(
        name="Tamarinier", local_name="Tamarin / Dakhar", scientific_name="Tamarindus indica",
        family="Fabaceae",
        description="Grand arbre aux gousses brunes contenant une pulpe acide très appréciée. Très résistant à la sécheresse.",
        habitat="Savanes, villages, zones semi-arides",
        regions="Nord (Korhogo, Ferkessédougou)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Boisson de tamarin (très populaire au Nord), condiment acide dans les sauces, bonbons.",
        medicinal_uses="Laxatif doux, traitement de la fièvre, riche en acide tartrique et vitamine C."
    ),

    # ── PLANTES DE RENTE ──────────────────────────────────────
    dict(
        name="Cacaoyer", local_name="Cacao", scientific_name="Theobroma cacao",
        family="Malvaceae",
        description="La Côte d'Ivoire est le premier producteur mondial de cacao. Ses cabosses contiennent les fèves servant à fabriquer le chocolat.",
        habitat="Sous-bois forestiers humides, plantations",
        regions="Centre-Ouest, Ouest, Sud (Yamoussoukro, Daloa, Soubré)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Fèves fermentées et séchées pour le chocolat, pulpe du fruit en jus, boisson de cacao local.",
        medicinal_uses="Théobromine (stimulant léger), antioxydants, beurre de cacao cicatrisant."
    ),
    dict(
        name="Caféier robusta", local_name="Café", scientific_name="Coffea canephora",
        family="Rubiaceae",
        description="Arbuste de la forêt équatoriale, l'un des piliers de l'économie ivoirienne. Côte d'Ivoire = 2ème producteur africain de café.",
        habitat="Forêts humides, plantations d'altitude",
        regions="Ouest (Man, Daloa, Gagnoa)",
        is_edible=True, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Grains torréfiés pour le café, fruits rouges (cerises) comestibles directement.",
        medicinal_uses="Stimulant (caféine), amélioration de la concentration, antioxydants."
    ),
    dict(
        name="Hévéa", local_name="Arbre à caoutchouc", scientific_name="Hevea brasiliensis",
        family="Euphorbiaceae",
        description="Source du caoutchouc naturel, culture en plein essor en Côte d'Ivoire. Son latex blanc est récolté par saignée de l'écorce.",
        habitat="Plantations, forêts humides",
        regions="Sud-Ouest (San-Pédro, Sassandra, Soubré)",
        is_edible=False, is_toxic=True, is_medicinal=False, is_invasive=False,
        toxicity_level="faible",
        culinary_uses="Non comestible. Latex industriel uniquement.",
        medicinal_uses="Peu d'usages médicinaux. Latex peut provoquer des allergies."
    ),

    # ── PLANTES ORNEMENTALES / COMMUNES ──────────────────────
    dict(
        name="Bougainvillée", local_name="Bougainvillier", scientific_name="Bougainvillea spectabilis",
        family="Nyctaginaceae",
        description="Liane ornementale aux bractées colorées (rose, rouge, orange, blanc) omniprésente dans les jardins et rues d'Abidjan.",
        habitat="Jardins, haies ornementales, zones urbaines",
        regions="Toute la Côte d'Ivoire (zones urbaines)",
        is_edible=False, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Non comestible. Plante purement ornementale.",
        medicinal_uses="Infusion de bractées contre la toux et les bronchites. Usage traditionnel contre l'hypertension."
    ),
    dict(
        name="Flamboyant", local_name="Arbre de feu", scientific_name="Delonix regia",
        family="Fabaceae",
        description="Arbre ornemental aux fleurs rouge écarlate spectaculaires, très planté dans les villes ivoiriennes. Fleurit en saison sèche.",
        habitat="Zones urbaines, avenues, jardins publics",
        regions="Abidjan et villes côtières",
        is_edible=False, is_toxic=False, is_medicinal=True, is_invasive=False,
        toxicity_level="aucun",
        culinary_uses="Graines parfois consommées après torréfaction dans certaines régions d'Afrique.",
        medicinal_uses="Décoction d'écorce contre le paludisme et la fièvre. Feuilles anti-inflammatoires."
    ),
    dict(
        name="Herbe à éléphant", local_name="Pennisetum / Napier", scientific_name="Pennisetum purpureum",
        family="Poaceae",
        description="Grande graminée pouvant atteindre 4m, très utilisée comme fourrage pour le bétail et pour stabiliser les sols.",
        habitat="Bords de routes, champs, zones humides",
        regions="Toute la Côte d'Ivoire",
        is_edible=False, is_toxic=False, is_medicinal=False, is_invasive=True,
        toxicity_level="aucun",
        culinary_uses="Non consommé par l'homme. Fourrage animal.",
        medicinal_uses="Peu d'usages médicinaux documentés."
    ),
    dict(
        name="Sensitive", local_name="Mimosa pudique / Herbe qui se cache", scientific_name="Mimosa pudica",
        family="Fabaceae",
        description="Petite plante rampante fascinante qui replie ses feuilles au moindre contact. Très connue des enfants ivoiriens.",
        habitat="Bords de chemins, pelouses, zones perturbées",
        regions="Toute la Côte d'Ivoire",
        is_edible=False, is_toxic=False, is_medicinal=True, is_invasive=True,
        toxicity_level="aucun",
        culinary_uses="Non comestible.",
        medicinal_uses="Racines utilisées contre l'insomnie et l'anxiété. Propriétés anti-inflammatoires et cicatrisantes."
    ),
    dict(
        name="Herbe de Guinée", local_name="Fétuque tropicale", scientific_name="Panicum maximum",
        family="Poaceae",
        description="Graminée haute très commune dans toute la zone tropicale ivoirienne, dominant les jachères et zones dégradées.",
        habitat="Savanes, jachères, bords de routes",
        regions="Toute la Côte d'Ivoire",
        is_edible=False, is_toxic=False, is_medicinal=False, is_invasive=True,
        toxicity_level="aucun",
        culinary_uses="Non consommé. Fourrage de qualité pour le bétail.",
        medicinal_uses="Aucun usage médicinal connu."
    ),
]


def seed():
    db = SessionLocal()
    inserted = 0
    skipped  = 0

    print(f"\n{'='*50}")
    print("  MikiPlants – Insertion des plantes CI")
    print(f"{'='*50}\n")

    for data in PLANTS:
        existing = db.query(Plant).filter(Plant.scientific_name == data["scientific_name"]).first()
        if existing:
            print(f"  [SKIP] {data['name']} (déjà en base)")
            skipped += 1
            continue
        plant = Plant(**data)
        db.add(plant)
        try:
            db.commit()
            print(f"  [OK]   {data['name']} ({data['scientific_name']})")
            inserted += 1
        except Exception as e:
            db.rollback()
            print(f"  [ERR]  {data['name']} : {e}")

    db.close()
    print(f"\n{'='*50}")
    print(f"  Terminé : {inserted} insérées, {skipped} ignorées")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    seed()
