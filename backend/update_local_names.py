import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
from database import SessionLocal
from models import Plant

UPDATES = {



    "Manihot esculenta": (
        "Bâkê (Baoulé) / Gnomi (Dioula) / Kpla (Bété) / Môkô (Attié) / "
        "Kplagba (Dida) / Yiridji (Senoufo)"
    ),
    "Manihot esculenta var. feuilles": (
        "Bâkê fêwê (Baoulé) / Gnomi fôlô (Dioula) / Kpla kpakpa (Bété) / "
        "Sakasaka (nom commun CI)"
    ),
    "Dioscorea rotundata": (
        "Bâkâ (Baoulé) / Yô (Dioula) / Kpa (Senoufo) / "
        "Bayèrè (Agni) / Wôkplô (Attié)"
    ),
    "Dioscorea cayennensis": (
        "Krenglê (Baoulé) / Yô jaune (Dioula) / Bâkâ blêblê (Agni)"
    ),
    "Dioscorea alata": (
        "Yam tchiê (Baoulé) / Yô tâ (Dioula) / Kpa djô (Senoufo)"
    ),
    "Musa paradisiaca": (
        "Djidji (Baoulé) / Korogo (Dioula) / Gbédji (Bété) / "
        "Bôdô (Agni) / Akwadu (Attié)"
    ),
    "Musa acuminata": (
        "Djidji dji (Baoulé) / Bananin (Dioula) / Gbédji dji (Bété) / "
        "Banana (Agni)"
    ),
    "Abelmoschus esculentus": (
        "Gnangnan (Baoulé) / Kanjà (Dioula) / Fêwê (Bété) / "
        "Nôgôn (Senoufo) / Okrô (Agni) / N'gôrôn (Attié)"
    ),
    "Solanum macrocarpon": (
        "Djakato (Baoulé) / Djèkpa (Dioula) / Kpli (Bété) / "
        "Njagato (Agni) / Gbêkpli (Attié)"
    ),
    "Solanum aethiopicum": (
        "Gnégué (Baoulé) / Djô-koungba (Dioula) / Kpli gbê (Bété) / "
        "Aubergine amère (CI)"
    ),
    "Ipomoea batatas": (
        "Wêrêwê (Baoulé) / Patata (Dioula) / Gbêtê (Bété) / "
        "Gbutôgbê (Senoufo) / Blétê (Agni)"
    ),
    "Solanum nigrum": (
        "Dêlê (Baoulé) / Gnégné (Dioula) / N'drowa (Attié) / "
        "Fêwê gnagnan (Bété) / Ntoté (Agni)"
    ),
    "Capsicum frutescens": (
        "Kpimi (Baoulé) / Foronto (Dioula) / Blô (Bété) / "
        "Yêrêkê (Senoufo) / Meko (Agni) / Ndjo (Attié)"
    ),
    "Capsicum annuum": (
        "Foronto dji (Dioula) / Kpimi dji (Baoulé) / "
        "Poivron (CI) / Blô dji (Bété)"
    ),
    "Colocasia esculenta": (
        "Kwa (Baoulé) / Kokoué (Dioula) / Gbêdê (Bété) / "
        "Toho (Senoufo) / Kôkô (Agni) / Yôkô (Attié)"
    ),
    "Xanthosoma sagittifolium": (
        "Koko (Baoulé) / Kokoué sauvage (Dioula) / Gbêdêgbê (Bété) / "
        "Macabo (CI)"
    ),
    "Arachis hypogaea": (
        "Kâkâ (Baoulé) / Djugu (Dioula) / Kpokpê (Bété) / "
        "Gwiri (Senoufo) / Nkate (Agni) / Djuguê (Attié)"
    ),
    "Vigna unguiculata": (
        "Abobô (Baoulé) / Sô (Dioula) / Nayiri (Senoufo) / "
        "Nzéma (Agni) / Wôrôwô (Bété)"
    ),
    "Phaseolus vulgaris": (
        "Tiê (Dioula) / Haricot (CI) / Adaba (Baoulé) / "
        "Fêwê tiê (Bété)"
    ),
    "Zea mays": (
        "Abodji (Baoulé) / Kâba (Dioula) / Blêblê (Bété) / "
        "Kaba (Senoufo) / Abodji (Agni) / Akôkô (Attié)"
    ),
    "Pennisetum glaucum": (
        "Sona (Senoufo) / Gana (Dioula) / Sanyo (Baoulé) / "
        "Mil de bouille (CI)"
    ),
    "Sorghum bicolor": (
        "Kâsâ (Senoufo) / Gnin (Dioula) / Kpêlê (Baoulé) / "
        "Goussi (Agni) / Sorgho rouge (CI)"
    ),
    "Oryza glaberrima": (
        "Mô (Dioula) / Mô (Baoulé) / Dô kple (Bété) / "
        "Riz africain (CI)"
    ),
    "Digitaria exilis": (
        "Foni (Dioula) / Tchio (Senoufo) / Fondo (CI) / "
        "Atchêkê (Baoulé)"
    ),
    "Cucumeropsis mannii": (
        "Kpèdê (Baoulé) / Kpê (Bété) / Egussi (Agni/CI) / "
        "Sô kpê (Dioula)"
    ),
    "Cucumis sativus": (
        "Kpata (Dioula) / Kokombre (CI) / Wô-wô kpê (Baoulé)"
    ),
    "Cucurbita pepo": (
        "Gbonflon (Baoulé) / Woro-woro kpê (Dioula) / Courge (CI)"
    ),
    "Cucurbita moschata": (
        "Gbonflon dji (Baoulé) / Woro-woro (Dioula) / "
        "Courge musquée (CI)"
    ),
    "Momordica charantia": (
        "Kô djimon (Dioula) / Margose (CI) / Kpêlê kpêlê (Baoulé) / "
        "Ntombo (Bété)"
    ),
    "Amaranthus hybridus": (
        "Fotê (Baoulé) / Bêtê (Dioula) / Blô-blô (Agni) / "
        "Fotê gbê (Bété)"
    ),
    "Amaranthus tricolor": (
        "Fotê kouman (Baoulé) / Bêtê blêblê (Dioula)"
    ),
    "Corchorus olitorius": (
        "Kpanlê (Baoulé) / Dah (Dioula) / Kpêtê (Bété) / "
        "Adémé (Agni)"
    ),
    "Celosia argentea": (
        "Fêwê blêblê (Baoulé) / Ntchô (Dioula) / Efo tête (CI) / "
        "Fotê-fotê (Agni)"
    ),
    "Nasturtium officinale": (
        "Watercress (CI) / Wô-wô fêwê (Baoulé)"
    ),
    "Petroselinum crispum": (
        "Ntchêlê (Dioula) / Persil (CI)"
    ),
    "Allium fistulosum": (
        "Tchiê (Dioula) / Civette (CI) / Gnon kpiti (Baoulé)"
    ),
    "Allium cepa": (
        "Gnon (Dioula) / Bâgnan (Baoulé) / Gnon gbê (Bété) / "
        "Gnon (Senoufo)"
    ),
    "Allium sativum": (
        "Tchi (Dioula) / Bâgnan tchi (Baoulé) / Ajo (CI)"
    ),


    "Ananas comosus": (
        "Gblê (Baoulé) / Nanas (Dioula) / Kpandjô (Agni) / "
        "Nanas (Attié) / Nanas (Bété)"
    ),
    "Carica papaya": (
        "Brofwê (Baoulé) / Papali (Dioula) / Kpoko (Bété) / "
        "Papayê (Agni) / Bôfwê (Attié)"
    ),
    "Mangifera indica": (
        "Mangwê (Baoulé) / Mangoro (Dioula) / Mangwê (Bété) / "
        "Manga (Agni) / Mangoro (Attié)"
    ),
    "Persea americana": (
        "Abokafwê (Baoulé) / Aboka (Dioula) / Poire (CI) / "
        "Aboka (Bété) / Pear (Agni)"
    ),
    "Psidium guajava": (
        "Wawayê (Baoulé) / Gwayaba (Dioula) / Kofi (Agni) / "
        "Goyave (Bété) / Gwayab (Attié)"
    ),
    "Citrus sinensis": (
        "Ôranci (Baoulé) / Lêmô (Dioula) / Oranje (Agni) / "
        "Lêmô (Bété)"
    ),
    "Citrus aurantiifolia": (
        "Citronin (Baoulé) / Lêmô wôrô (Dioula) / Nzan lêmô (Agni) / "
        "Citron (Bété)"
    ),
    "Citrus reticulata": (
        "Lêmô dji (Baoulé) / Mandarin (Dioula) / Mandarine (CI)"
    ),
    "Citrus maxima": (
        "Pamplêmus (Baoulé) / Shaddock (Agni) / Gros lêmô (Dioula)"
    ),
    "Annona muricata": (
        "Bêrêfê (Baoulé) / Gnamakôdji (Dioula) / Apôsô (Agni) / "
        "Soursop (CI) / Gbinni (Bété)"
    ),
    "Annona squamosa": (
        "Kankê (Baoulé) / Pomme-kankê (Dioula) / "
        "Pomme cannelle (CI) / Afôdji (Agni)"
    ),
    "Manilkara zapota": (
        "Sapoti (Dioula) / Nêfle (CI) / Chiku (Agni)"
    ),
    "Averrhoa carambola": (
        "Blonkôfwê (Baoulé) / Lêmô tcha (Dioula) / "
        "Carambole-étoile (CI)"
    ),
    "Tamarindus indica": (
        "Tomi (Dioula) / Tomi wê (Baoulé) / Dago (Senoufo) / "
        "Tamarin (CI) / Koumba (Agni)"
    ),
    "Ziziphus mauritiana": (
        "Ntontoê (Baoulé) / Sihi (Dioula) / Jujubier (CI) / "
        "Kuntunmani (Senoufo)"
    ),
    "Adansonia digitata": (
        "Zan (Baoulé) / Bohi (Dioula) / Kûnyalô (Senoufo) / "
        "Bohi djiri (CI)"
    ),
    "Artocarpus heterophyllus": (
        "Djatôfwê (Baoulé) / Jaka (Dioula) / Jacque (CI)"
    ),
    "Artocarpus altilis": (
        "Lebê (Baoulé) / Pain d'arbre (CI) / Abrodô (Agni)"
    ),
    "Muntingia calabura": (
        "Akpi tchi (Agni) / Cerise tropicale (CI) / Besonti (Baoulé)"
    ),


    "Azadirachta indica": (
        "Korobâ (Dioula) / Nim (Baoulé) / Pèm (Senoufo) / "
        "Margousier (CI) / Nim yiri (CI)"
    ),
    "Moringa oleifera": (
        "Néverdié (Dioula) / Nokondin (Baoulé) / Kuli kuli yiri (Senoufo) / "
        "Arbre miracle (CI)"
    ),
    "Vernonia amygdalina": (
        "Kponan (Baoulé) / Djèkpa gnin (Dioula) / Gnanfon-fon (Bété) / "
        "Ewuro (Yoruba/CI)"
    ),
    "Cymbopogon citratus": (
        "Tiêman (Dioula) / Wô-wô (Baoulé) / Gbê-tiêman (Bété) / "
        "Herbe citron (CI)"
    ),
    "Ocimum gratissimum": (
        "Ntchêdji (Dioula) / Kébê-kébê (Baoulé/CI) / Ntcho-ntcho (Bété) / "
        "Efirin (Yoruba/CI)"
    ),
    "Ocimum tenuiflorum": (
        "Efirin pupa (Yoruba) / Kébê-kébê rouge (CI) / Tulsi (CI)"
    ),
    "Mentha viridis": (
        "Mintê (Dioula) / Menthe (CI) / Mintê fêwê (Baoulé)"
    ),
    "Aloe vera": (
        "Zavila (Dioula) / Gbêmbê-zavila (Baoulé) / "
        "Gindê (Senoufo) / Aloès (CI)"
    ),
    "Zingiber officinale": (
        "Jinja (Dioula) / Ginjanin (Baoulé) / Kpinêkin (Bété) / "
        "Djinja (Senoufo) / Tangawisi (Swahili/CI)"
    ),
    "Curcuma longa": (
        "Kulkul (Dioula) / Kulukulin (Baoulé) / Safran des Indes (CI)"
    ),
    "Artemisia annua": (
        "Armoise africaine (CI) / Tikôtchê (Dioula) / "
        "Zômlê (Baoulé)"
    ),
    "Kalanchoe pinnata": (
        "Dolidjiri fêwê (Dioula) / Gbêmbê kpli (Baoulé) / "
        "Herbe de vie (CI) / Rapadou (Agni)"
    ),
    "Cymbopogon nardus": (
        "N'drê (Dioula) / Wô-wô gbê (Baoulé) / Citronnelle rouge (CI)"
    ),
    "Senna siamea": (
        "Séné (Dioula) / Kassié (Baoulé) / Kassié yiri (CI)"
    ),
    "Ricinus communis": (
        "Kpakpaya (Dioula) / Gbêmbê ngui (Baoulé) / Gblo-gblo (Bété) / "
        "Soho (Senoufo) / Ricin (CI)"
    ),
    "Datura stramonium": (
        "Djinè wolo (Dioula) / Awlibwê klan (Baoulé) / "
        "Herbe du diable (CI)"
    ),
    "Euphorbia tirucalli": (
        "Kêlêfê (Dioula) / Gbê-kêlê (Baoulé) / Arbre cierge (CI)"
    ),
    "Solanum torvum": (
        "Gnégné sauvage (CI) / Sooro (Dioula) / Gnamankoudji gbê (Baoulé)"
    ),
    "Catharanthus roseus": (
        "Vinca rose (CI) / Fleur pervenche (Baoulé) / Dêlê wôlê (Dioula)"
    ),
    "Cyperus papyrus": (
        "Wô kpli (Baoulé) / Roseau des marais (CI) / Sô wô (Dioula)"
    ),


    "Milicia excelsa": (
        "Séwê (Baoulé) / Kambala (Dioula) / Lok (Attié) / "
        "Iroko (CI) / Lusinga (Bété)"
    ),
    "Entandrophragma utile": (
        "Etouali (Attié) / Sipo (CI) / Blêgbo (Baoulé)"
    ),
    "Entandrophragma cylindricum": (
        "Abêbê (Attié) / Sapelli (CI) / Blêgbo kpiti (Baoulé)"
    ),
    "Khaya ivorensis": (
        "Khaya (Attié) / Acajou (CI) / Gbêtê yiri (Baoulé) / "
        "Djalidjiri (Dioula)"
    ),
    "Terminalia superba": (
        "Emien (Attié) / Fraké (CI) / Fabrê (Baoulé) / Limba (CI)"
    ),
    "Tectona grandis": (
        "Diala (Dioula) / Teck (CI) / Séré yiri (Baoulé)"
    ),
    "Eucalyptus camaldulensis": (
        "Kaliptus (Dioula) / Eucalyptus (CI) / Kaliptus yiri (Baoulé)"
    ),
    "Parkia biglobosa": (
        "Daw (Dioula) / Nêlê (Senoufo) / Nêrê (CI) / "
        "Nêrê yiri (Baoulé) / Nêtê (Agni)"
    ),
    "Pterocarpus erinaceus": (
        "Vêné (CI) / Guéno (Dioula) / Vêné yiri (Baoulé)"
    ),
    "Milicia excelsa": (
        "Séwê (Baoulé) / Kambala (Dioula) / Lok (Attié)"
    ),


    "Theobroma cacao": (
        "Koko (Baoulé) / Kaka (Dioula) / Kpô (Bété) / "
        "Kakao (Agni) / Cacao (CI)"
    ),
    "Coffea canephora": (
        "Kafê (Dioula) / Kafê yiri (Baoulé) / Kafê (Bété) / "
        "Caféier robusta (CI)"
    ),
    "Coffea arabica": (
        "Kafê arabika (Dioula) / Kafê gnin (CI) / Kafê doux (CI)"
    ),
    "Hevea brasiliensis": (
        "Kôrôdji (Baoulé) / Kôrôdji yiri (Dioula) / Gôlê yiri (Bété) / "
        "Caoutchouc (CI)"
    ),
    "Elaeis guineensis": (
        "Ngui (Baoulé) / Sèguèlè (Dioula) / Gbê (Bété) / "
        "Kpê (Attié) / Abe (Agni) / Palmier CI"
    ),
    "Gossypium hirsutum": (
        "Kotê (Dioula) / Tchio (Senoufo) / Gbê-gbê (Baoulé) / "
        "Coton (CI)"
    ),
    "Anacardium occidentale": (
        "Kajou (Dioula) / Akajou (Baoulé) / Kachew (Agni) / "
        "Noix de cajou (CI)"
    ),
    "Cola nitida": (
        "Woro (Dioula) / Bii (Baoulé) / Ola (Attié) / "
        "Gbopê (Bété) / Gourou (CI) / Kola (Agni)"
    ),
    "Vitellaria paradoxa": (
        "Sii (Dioula) / Fulê (Baoulé) / Ntché (Bété) / "
        "Kpêkê (Senoufo) / Karité (CI)"
    ),


    "Eichhornia crassipes": (
        "Wô-wô kôrôgô (Dioula) / N'nzê wô (Baoulé) / "
        "Jacinthe d'eau (CI)"
    ),
    "Pistia stratiotes": (
        "Wô-kpli (Baoulé) / Foulê-wô (Dioula) / Laitue d'eau (CI)"
    ),
    "Nymphaea lotus": (
        "Wô blêblê (Baoulé) / Lotus blanc (CI) / Wô-wô dji (Dioula)"
    ),


    "Xylopia aethiopica": (
        "Soubara (Dioula) / Kani (Baoulé/Agni) / Êtô (Attié) / "
        "Wama (Senoufo) / Poivre pays (CI)"
    ),
    "Xylopia parviflora": (
        "Yiri tchêtchê (Baoulé) / Djar (Dioula) / "
        "Sélim sauvage (CI)"
    ),
    "Cinnamomum verum": (
        "Kinamon (Dioula) / Cannelle (CI) / Kinnamon (Baoulé)"
    ),
    "Aframomum melegueta": (
        "Atariko (Yoruba/CI) / Akudjura (CI) / Eferi (Agni) / "
        "Maniguette (CI) / Graines de paradis (CI)"
    ),
    "Piper nigrum": (
        "Kologna (Dioula) / Poivre (CI) / Kolognan (Baoulé)"
    ),
    "Piper guineense": (
        "Gbafilo (Dioula) / Poivre long (CI) / Êsoê (Attié) / "
        "Poivre Ashanti (CI)"
    ),
    "Hibiscus sabdariffa": (
        "Wonjo (Dioula) / Dabileni (Senoufo) / Bissap (CI) / "
        "Foléré (Nord CI) / Wôrôwô (Baoulé)"
    ),
    "Sesamum indicum": (
        "Bêni (Dioula) / Gbêlo (Baoulé) / Sésame (CI) / "
        "Sesam (Agni)"
    ),


    "Hibiscus rosa-sinensis": (
        "Kêkê wulên (Baoulé) / Fleur chaussure (CI) / "
        "Fleur d'un jour (CI)"
    ),
    "Codiaeum variegatum": (
        "Wôlê kpê (Baoulé) / Croton (CI)"
    ),
    "Plumeria rubra": (
        "Franjipanier (CI) / Fleur pompe funèbre (CI) / "
        "Gbêwôlê tchi (Baoulé)"
    ),
    "Canna indica": (
        "Têlê tchi (Dioula) / Balisier (CI) / Fleur canna (CI)"
    ),
    "Lantana camara": (
        "Gnangoê (Baoulé) / Tchi-tchi (CI) / Gbansô (Dioula) / "
        "Buisson ardent (CI)"
    ),
    "Bougainvillea spectabilis": (
        "Fleur papier (CI) / Bougainvillier (CI) / Wôlê-kpê blêblê (Baoulé)"
    ),
    "Delonix regia": (
        "Gbêkô yiri (Dioula) / Blêblê yiri (Baoulé) / "
        "Flamboyant (CI) / Arbre de feu (CI)"
    ),


    "Ceiba pentandra": (
        "Woî (Baoulé) / Konkoré (Dioula) / Gbê-woro (Bété) / "
        "Lokô (Attié) / Fromager (CI)"
    ),
    "Borassus aethiopum": (
        "Boré (Baoulé) / Boro (Dioula) / Kworo (Senoufo) / "
        "Nzonzô (Agni) / Rônier (CI)"
    ),
    "Raphia hookeri": (
        "Pan (Attié) / Raphia (CI) / Gnin-gnin wô (Dioula) / "
        "Wôrô (Baoulé)"
    ),


    "Pennisetum purpureum": (
        "Gbê gbê (Baoulé) / Sô gbê (Dioula) / Herbe éléphant (CI)"
    ),
    "Panicum maximum": (
        "Sô gnin (Dioula) / Panakin sô (CI) / Sô gbê (Baoulé)"
    ),
    "Saccharum officinarum": (
        "Fomê (Baoulé) / Sukari (Dioula) / Kêrêtê (Bété) / "
        "Sôkô (Agni) / Canne à sucre (CI)"
    ),
    "Bambusa vulgaris": (
        "Bambu (Dioula) / Wôlê (Baoulé) / Bambou commun (CI)"
    ),


    "Mimosa pudica": (
        "Tomaô (Dioula) / Kôkôrôkô (Baoulé) / Gbê-kpêlê (Bété) / "
        "Sensitive (CI)"
    ),


    "Acacia senegal": (
        "Séguélé (Dioula) / Gnin-gnin (Senoufo) / Gonakier (CI)"
    ),
    "Acacia seyal": (
        "Ganna woyo (Dioula) / Épineux rouge (CI) / Sô-sô (Senoufo)"
    ),
    "Acacia nilotica": (
        "Babul (Dioula) / Gonakier épineux (CI) / Naara (Senoufo)"
    ),
    "Prosopis africana": (
        "Wasota (Dioula) / Prosopis (CI) / N'biridji (Senoufo)"
    ),


    "Detarium microcarpum": (
        "Dattier du Sénégal (CI) / Gbê kpê (Dioula) / "
        "Détarium (CI)"
    ),
    "Lannea acida": (
        "Gnon tété (Dioula) / Raisinier sauvage (CI) / "
        "Lannée (Baoulé)"
    ),
    "Combretum micranthum": (
        "Kinkiliba (Dioula) / Sô-sô (Senoufo) / Raisinier (CI)"
    ),
    "Ziziphus mucronata": (
        "Sihi gnin (Dioula) / Jujubier sauvage (CI)"
    ),
    "Cola acuminata": (
        "Kola garoukê (CI) / Wolo dji (Dioula) / Faux cola (CI)"
    ),
    "Cola lateritia": (
        "Wolo-ji (Dioula) / Arbre-kola (CI) / Kolatier (Baoulé)"
    ),
    "Daniellia oliveri": (
        "Santan (Dioula) / Faux karité (CI) / Gbêtê yiri dji (Baoulé)"
    ),
    "Piliostigma thonningii": (
        "Tonzonmon (Dioula) / Camel's foot (CI) / Gbêtê-gbêtê (Baoulé)"
    ),
    "Ficus gnaphalocarpa": (
        "Tèni (Dioula) / Figuier sacré (CI) / Séwê djiri (Baoulé)"
    ),
    "Ficus sur": (
        "Sossê (Baoulé) / Tèni sauvage (Dioula) / Figuier sauvage (CI)"
    ),
    "Bombax buonopozense": (
        "Gbondou (Baoulé) / Pochote (CI) / Kpê-kpê (Dioula) / "
        "Fromager rouge (CI)"
    ),
    "Nauclea latifolia": (
        "Gbêlê (Baoulé) / African peach (CI) / Ndjihi (Dioula)"
    ),
    "Pterocarpus santalinoides": (
        "Kpaô (Dioula) / Padouk d'eau (CI) / Gbêtê wô (Baoulé)"
    ),
    "Lophira alata": (
        "Azobé (CI) / Bêlê (Baoulé) / Efulê (Attié)"
    ),
    "Parinari excelsa": (
        "Abêni (Attié) / Gingerbread tree (CI) / Gbô-gbô (Baoulé)"
    ),
    "Oncoba spinosa": (
        "Kpêklê (Baoulé) / Snuff box tree (CI) / Dê-dê (Dioula)"
    ),
    "Aucoumea klaineana": (
        "Okoumé (CI) / Adjounbou (Attié)"
    ),


    "Jatropha curcas": (
        "Gbongni (Dioula) / Gbêtê ngui (Baoulé) / Pina yiri (Senoufo) / "
        "Pourghère (CI)"
    ),
    "Lippia multiflora": (
        "Fio-fio (CI) / Tisane de savane / N'tô (Dioula) / "
        "Verbêna (Baoulé)"
    ),
    "Lippia javanica": (
        "Tchêman (Dioula) / Thym africain (CI) / Mintê yiri (Baoulé)"
    ),


    "Termitomyces robustus": (
        "Gnêhi (Baoulé) / Kpandjê (Agni) / Champignon de termite (CI) / "
        "Gnêhi gbê (Dioula)"
    ),
    "Termitomyces striatus": (
        "Gnêhi kpiti (Baoulé) / Champignon termite petit (CI)"
    ),
}


def update():
    db = SessionLocal()
    updated = 0
    not_found = []

    print()
    print("=" * 60)
    print("  MikiPlants — Mise à jour des noms locaux")
    print("=" * 60)
    print()

    for sci_name, new_local_name in UPDATES.items():
        plant = db.query(Plant).filter(
            Plant.scientific_name == sci_name
        ).first()

        if plant:
            old = plant.local_name or ""
            plant.local_name = new_local_name
            updated += 1
            print(f"  [OK] {plant.name}")
            print(f"       Avant : {old[:70]}{'...' if len(old) > 70 else ''}")
            print(f"       Après : {new_local_name[:70]}{'...' if len(new_local_name) > 70 else ''}")
            print()
        else:
            not_found.append(sci_name)

    db.commit()
    db.close()

    print("=" * 60)
    print(f"  Mis à jour : {updated} plantes")
    if not_found:
        print(f"  Non trouvées ({len(not_found)}) :")
        for n in not_found:
            print(f"    - {n}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    update()
