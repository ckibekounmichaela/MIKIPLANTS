# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from database import SessionLocal
from models import Plant

NOMS = {
    "Manihot esculenta":               "manioc",
    "Manihot esculenta var. feuilles": "feuilles de manioc",
    "Dioscorea rotundata":             "igname blanche",
    "Dioscorea cayennensis":           "igname jaune",
    "Dioscorea alata":                 "igname de trois mois",
    "Musa paradisiaca":                "plantain",
    "Musa acuminata":                  "banane douce",
    "Abelmoschus esculentus":          "gombo",
    "Solanum macrocarpon":             "gnangnan",
    "Solanum aethiopicum":             "aubergine amere",
    "Ipomoea batatas":                 "patate douce",
    "Solanum nigrum":                  "gnegne",
    "Capsicum frutescens":             "piment",
    "Capsicum annuum":                 "poivron",
    "Colocasia esculenta":             "taro",
    "Xanthosoma sagittifolium":        "macabo",
    "Arachis hypogaea":                "arachide",
    "Vigna unguiculata":               "niebe",
    "Phaseolus vulgaris":              "haricot vert",
    "Zea mays":                        "mais",
    "Pennisetum glaucum":              "mil",
    "Sorghum bicolor":                 "sorgho",
    "Oryza glaberrima":                "riz de plateau",
    "Digitaria exilis":                "fonio",
    "Cucumeropsis mannii":             "graines de courge",
    "Cucumis sativus":                 "concombre",
    "Cucurbita pepo":                  "courgette",
    "Cucurbita moschata":              "courge musquee",
    "Momordica charantia":             "margose",
    "Amaranthus hybridus":             "amarante",
    "Amaranthus tricolor":             "amarante tricolore",
    "Corchorus olitorius":             "kplala",
    "Celosia argentea":                "epinard africain",
    "Nasturtium officinale":           "cresson",
    "Petroselinum crispum":            "persil",
    "Allium fistulosum":               "ciboulette",
    "Allium cepa":                     "oignon",
    "Allium sativum":                  "ail",
    "Ananas comosus":                  "ananas",
    "Carica papaya":                   "papaye",
    "Mangifera indica":                "mangue",
    "Persea americana":                "avocat",
    "Psidium guajava":                 "goyave",
    "Citrus sinensis":                 "orange",
    "Citrus aurantiifolia":            "citron vert",
    "Citrus reticulata":               "mandarine",
    "Citrus maxima":                   "pamplemousse",
    "Annona muricata":                 "corossol",
    "Annona squamosa":                 "pomme cannelle",
    "Manilkara zapota":                "sapotille",
    "Averrhoa carambola":              "carambole",
    "Tamarindus indica":               "tamarin",
    "Ziziphus mauritiana":             "jujube",
    "Adansonia digitata":              "pain de singe",
    "Artocarpus heterophyllus":        "jacque",
    "Artocarpus altilis":              "arbre a pain",
    "Muntingia calabura":              "cerise tropicale",
    "Azadirachta indica":              "nim",
    "Moringa oleifera":                "moringa",
    "Vernonia amygdalina":             "feuille amere",
    "Cymbopogon citratus":             "herbe citron",
    "Ocimum gratissimum":              "kebe-kebe",
    "Ocimum tenuiflorum":              "basilic sacre",
    "Mentha viridis":                  "menthe",
    "Aloe vera":                       "aloes",
    "Zingiber officinale":             "gingembre",
    "Curcuma longa":                   "curcuma",
    "Artemisia annua":                 "artemisia",
    "Kalanchoe pinnata":               "herbe de vie",
    "Cymbopogon nardus":               "citronnelle rouge",
    "Senna siamea":                    "kassie",
    "Ricinus communis":                "pourgh\u00e8re",
    "Jatropha curcas":                 "pourgh\u00e8re sauvage",
    "Datura stramonium":               "herbe du diable",
    "Euphorbia tirucalli":             "arbre cierge",
    "Solanum torvum":                  "gnegne sauvage",
    "Catharanthus roseus":             "vinca rose",
    "Cyperus papyrus":                 "papyrus",
    "Milicia excelsa":                 "iroko",
    "Entandrophragma utile":           "sipo",
    "Entandrophragma cylindricum":     "sapelli",
    "Khaya ivorensis":                 "acajou",
    "Terminalia superba":              "frake",
    "Tectona grandis":                 "teck",
    "Eucalyptus camaldulensis":        "eucalyptus",
    "Parkia biglobosa":                "nere",
    "Pterocarpus erinaceus":           "vene",
    "Lophira alata":                   "azobe",
    "Daniellia oliveri":               "faro de savane",
    "Piliostigma thonningii":          "pied de chameau",
    "Ficus gnaphalocarpa":             "figuier sacre",
    "Ficus sur":                       "figuier sauvage",
    "Bombax buonopozense":             "fromager rouge",
    "Nauclea latifolia":               "pecher africain",
    "Pterocarpus santalinoides":       "padouk d eau",
    "Parinari excelsa":                "parinari",
    "Oncoba spinosa":                  "oncoba",
    "Aucoumea klaineana":              "okoume",
    "Theobroma cacao":                 "cacao",
    "Coffea canephora":                "cafe robusta",
    "Coffea arabica":                  "cafe arabica",
    "Hevea brasiliensis":              "hevea",
    "Elaeis guineensis":               "palmier a huile",
    "Gossypium hirsutum":              "coton",
    "Anacardium occidentale":          "noix de cajou",
    "Cola nitida":                     "noix de kola",
    "Vitellaria paradoxa":             "karite",
    "Xylopia aethiopica":              "poivre de Guinee",
    "Xylopia parviflora":              "selim sauvage",
    "Cinnamomum verum":                "cannelle",
    "Aframomum melegueta":             "maniguette",
    "Piper nigrum":                    "poivre noir",
    "Piper guineense":                 "poivre long africain",
    "Hibiscus sabdariffa":             "bissap",
    "Sesamum indicum":                 "sesame",
    "Hibiscus rosa-sinensis":          "fleur chaussure",
    "Codiaeum variegatum":             "croton",
    "Plumeria rubra":                  "frangipanier",
    "Canna indica":                    "balisier",
    "Lantana camara":                  "gattilier",
    "Bougainvillea spectabilis":       "bougainvillier",
    "Delonix regia":                   "flamboyant",
    "Ceiba pentandra":                 "fromager",
    "Borassus aethiopum":              "ronier",
    "Raphia hookeri":                  "raphia",
    "Saccharum officinarum":           "canne a sucre",
    "Bambusa vulgaris":                "bambou",
    "Acacia senegal":                  "gonakier",
    "Acacia seyal":                    "epineux rouge",
    "Acacia nilotica":                 "gonakier epineux",
    "Prosopis africana":               "prosopis africain",
    "Detarium microcarpum":            "dattier du Senegal",
    "Lannea acida":                    "raisinier sauvage",
    "Combretum micranthum":            "kinkiliba",
    "Ziziphus mucronata":              "jujubier sauvage",
    "Cola acuminata":                  "faux kola",
    "Cola lateritia":                  "kolatier",
    "Pennisetum purpureum":            "herbe elephant",
    "Panicum maximum":                 "herbe de Guinee",
    "Eichhornia crassipes":            "jacinthe d eau",
    "Pistia stratiotes":               "salade d eau douce",
    "Nymphaea lotus":                  "nenuphar blanc",
    "Mimosa pudica":                   "sensitive",
    "Lippia multiflora":               "verveine sauvage",
    "Lippia javanica":                 "thym africain",
    "Termitomyces robustus":           "champignon de termitiere",
    "Termitomyces striatus":           "petit champignon de termite",
}

db = SessionLocal()
updated = 0
not_found = []

print("=== MikiPlants - Reset noms CI ===")

for sci, nom in NOMS.items():
    p = db.query(Plant).filter(Plant.scientific_name == sci).first()
    if p:
        p.local_name = nom
        updated += 1
        print(f"[OK] {p.name} -> {nom}")
    else:
        not_found.append(sci)

db.commit()
db.close()

print(f"\nMis a jour : {updated} plantes")
if not_found:
    print(f"Non trouvees : {len(not_found)}")
    for n in not_found:
        print(f"  - {n}")
print("=== Termine ===")
