import subprocess
import os
import json
import re
import logging

logger = logging.getLogger("INN_TOp.OCR")

import urllib.request
import urllib.parse
import urllib.error
import traceback

# Lazy load EasyOCR reader so it doesn't freeze the app on startup
_EASYOCR_READER = None

def get_easyocr_reader():
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        try:
            import easyocr
            logger.info("EasyOCR modelini yuklash boshlandi (bu biroz vaqt olishi mumkin)...")
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _EASYOCR_READER = easyocr.Reader(['ru', 'en'])
            logger.info("EasyOCR modeli muvaffaqiyatli yuklandi.")
        except ImportError:
            logger.warning("easyocr kutubxonasi topilmadi. Mahalliy (Local) OCR ishlashida xato bo'lishi mumkin.")
            return None
    return _EASYOCR_READER

def extract_text_from_image_online(image_path, api_key='helloworld'):
    """
    Uses the free OCR.space API to extract text.
    Fallback when local OCR fails.
    """
    logger.info("Attempting Online OCR (OCR.space)...")
    try:
        url = 'https://api.ocr.space/parse/image'
        
        # Read file binary
        with open(image_path, 'rb') as f:
            file_bytes = f.read()
            
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        data = []
        data.append(f'--{boundary}')
        data.append('Content-Disposition: form-data; name="apikey"')
        data.append('')
        data.append(api_key)
        data.append(f'--{boundary}')
        data.append('Content-Disposition: form-data; name="language"')
        data.append('')
        data.append('rus') # Changed from 'eng' to 'rus' to support Cyrillic + English
        data.append(f'--{boundary}')
        data.append('Content-Disposition: form-data; name="file"; filename="image.png"')
        data.append('Content-Type: image/png')
        data.append('')
        # Binary data needs to be handled carefully in joining, better to use standard libraries or simple concatenation
        # But standard urllib doesn't do multipart easily. 
        # Simplified: We will use a dedicated multipart helper or just simpler approach if possible.
        # Actually, let's just use the 'base64Image' parameter of OCR.space! It's easier specifically for no-dep.
        pass
    except Exception:
        pass

    # Easier approach: Base64
    import base64
    try:
        with open(image_path, "rb") as image_file:
            base64_bytes = base64.b64encode(image_file.read()).decode('utf-8')
            base64_string = f"data:image/png;base64,{base64_bytes}"
            
        post_data = urllib.parse.urlencode({
            'apikey': api_key,
            'base64Image': base64_string,
            'language': 'rus', # Changed from 'eng' to 'rus'
            'isOverlayRequired': False,
            'scale': True,
            'OCREngine': 2
        }).encode('ascii')
        
        req = urllib.request.Request(url, data=post_data)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        if result.get('IsErroredOnProcessing'):
             logger.error(f"Online OCR Error: {result.get('ErrorMessage')}")
             return ""
             
        parsed_results = result.get('ParsedResults')
        if parsed_results:
            text = parsed_results[0].get('ParsedText')
            logger.info("Online OCR Success!")
            return text
            
    except Exception as e:
        logger.error(f"Online OCR Failed: {e}")
        
    return ""

def extract_text_from_image(image_path):
    """Executes the Local EasyOCR python package to extract text. Falls back to Online if failed."""
    local_text = ""
    
    # 1. Try Local EasyOCR
    logger.info(f"Mahalliy (Local) OCR orqali rasm o'qilmoqda: {image_path}")
    try:
        reader = get_easyocr_reader()
        if reader is not None:
            results = reader.readtext(image_path, detail=0)
            local_text = " ".join(results)
            
            if local_text.strip():
                logger.debug(f"Local OCR Result:\n{local_text}")
                return local_text
            else:
                logger.warning("Local OCR bo'sh natija qaytardi. Fallback qilinmoqda...")
        else:
            logger.warning("Local OCR modeli yuklanmadi. Fallback qilinmoqda...")
    except Exception as e:
        logger.exception("Mahalliy (Local) OCR ishlashda xatolikka yo'l qo'ydi.")

    # 2. Fallback to Online
    return extract_text_from_image_online(image_path)

def normalize_text(text):
    """Normalizes text by replacing Cyrillic characters with Latin lookalikes and other common OCR fixes."""
    # Correct Phonetic Transliteration for Uzbek Cyrillic -> Latin
    replacements = {
        'а': 'a', 'А': 'A', 'б': 'b', 'Б': 'B', 'в': 'v', 'В': 'V', 'г': 'g', 'Г': 'G',
        'д': 'd', 'Д': 'D', 'е': 'e', 'Е': 'E', 'ё': 'yo', 'Ё': 'Yo', 'ж': 'j', 'Ж': 'J',
        'з': 'z', 'З': 'Z', 'и': 'i', 'И': 'I', 'й': 'y', 'Й': 'Y', 'к': 'k', 'К': 'K',
        'л': 'l', 'Л': 'L', 'м': 'm', 'М': 'M', 'н': 'n', 'Н': 'N', 'о': 'o', 'О': 'O',
        'п': 'p', 'П': 'P', 'р': 'r', 'Р': 'R', 'с': 's', 'С': 'S', 'т': 't', 'Т': 'T',
        'у': 'u', 'У': 'U', 'ф': 'f', 'Ф': 'F', 'х': 'x', 'Х': 'X', 'ц': 'ts', 'Ц': 'Ts',
        'ч': 'ch', 'Ч': 'Ch', 'ш': 'sh', 'Ш': 'Sh', 'щ': 'sh', 'Щ': 'Sh', 'ъ': "'", 
        'ы': 'y', 'Ы': 'Y', 'ь': '', 'э': 'e', 'Э': 'E', 'ю': 'yu', 'Ю': 'Yu', 'я': 'ya', 'Я': 'Ya',
        'ў': "o'", 'Ў': "O'", 'қ': 'q', 'Қ': 'Q', 'ғ': "g'", 'Ғ': "G'", 'ҳ': 'h', 'Ҳ': 'H',
        
        
        # Common word fixes
        'укуний': 'umumiy', 'тамлим': "ta'lim", 'мактаби': 'maktabi', 'nohj': 'mchj'
    }
    normalized = text
    for cyr, lat in replacements.items():
        normalized = normalized.replace(cyr, lat)
    
    # Advanced Regex Normalization
    # "3 maktab" -> "3-sonli maktab"
    normalized = re.sub(r'\b(\d+)\s+maktab\b', r'\1-sonli maktab', normalized)
    
    # Clean up whitespace and newlines for better exact matching
    normalized = normalized.replace('\n', ' ').replace('\r', '')
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def find_inn_in_text(text):
    """Searches for a 9-digit INN in the text."""
    logger.debug("Searching for INN in text...")
    
    # 1. Try standard continuous 9 digits
    match = re.search(r'\b\d{9}\b', text)
    if match: 
        logger.info(f"INN found (exact): {match.group(0)}")
        return match.group(0)

    # 2. Try identifying numbers with spaces/dashes (e.g. 200 123 456)
    lenient_matches = re.findall(r'\d[\d\s-]{7,15}\d', text)
    
    for m in lenient_matches:
        digits = re.sub(r'\D', '', m)
        if len(digits) == 9:
            logger.info(f"INN found (fuzzy): {digits} from '{m}'")
            return digits
            
    logger.info("No INN found.")
    return None

import difflib

def find_organization_in_text(text):
    """Searches for organization names from data.json in the text. Returns (name, inn, person_name, phone)."""
    if not text: return None, None, None, None
    
    logger.debug("Searching for Organization Name in text...")
    
    # Load Data
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_path, "data.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e: 
        logger.error(f"Failed to load data.json: {e}")
        return None, None, None, None

    # Normalize extracted text
    text_clean = normalize_text(text.lower())
    logger.debug(f"Normalized Text for search: {text_clean}")
    
    text_words = re.findall(r'\w+', text_clean)
    
    best_match = None
    best_score = 0
    best_inn = None
    best_person = None
    best_phone = None
    
    for item in data:
        # NEW STRUCTURE: 'm' is the name (Mahalla/Maktab name)
        name = item.get("m", "")
        person = item.get("f", "")
        phone = item.get("t", "")
        inn_val = item.get("inn", "")
        
        current_score = 0
        match_source = "name" # or "person"
        
        # --- 1. PERSON NAME MATCHING (High Priority) ---
        if person:
            person_lower = person.lower()
            # Remove "v/b" or similar prefixes if any, though likely not needed for simple split
            p_words = re.findall(r'[a-z]{3,}', person_lower) # only words 3+ chars
            
            if p_words:
                p_matches = 0
                for pw in p_words:
                     # Check approximate match
                     if pw in text_clean:
                         p_matches += 1
                     else:
                         # Fuzzy check
                         if difflib.get_close_matches(pw, text_words, n=1, cutoff=0.85):
                             p_matches += 1
                
                # If we have multiple words (e.g. First Last Patronymic), matching 2 is very strong.
                # If only 1 word, it might be common name, so be careful.
                if len(p_words) >= 2 and p_matches >= 2:
                    current_score = 2000 + (p_matches * 100) # Higher than any name match
                    match_source = "person"
                elif len(p_words) == 1 and p_matches == 1:
                    # Weak match, only use if name match is also present or as tie breaker
                    current_score = 50 

        # --- 2. ORGANIZATION NAME MATCHING ---
        if current_score < 2000 and name:
            name_lower = name.lower()
            
            # Strict Number Check
            org_nums = re.findall(r'\d+', name_lower)
            text_nums = re.findall(r'\d+', text_clean)
            
            skip_name_check = False
            if org_nums:
                # Check for intersection. If specific numbers are in Org Name, 
                # at least one of them MUST be in the Text.
                if not set(org_nums) & set(text_nums):
                     skip_name_check = True

            if not skip_name_check:
                # Exact substring match (Highest Priority for name)
                if name_lower in text_clean:
                    name_score = 1000
                else:
                    # Fuzzy Word Matching
                    org_words = re.findall(r'\d+|[a-z]+', name_lower)
                    if org_words:
                        matches = 0
                        valid_word_count = 0
                        
                        for org_w in org_words:
                            # Allow numbers of any length, but text must match words >= 3 chars
                            if len(org_w) < 3 and not org_w.isdigit(): continue
                            valid_word_count += 1
                            
                            # Check for direct match or fuzzy match in text words
                            if org_w in text_clean:
                                matches += 1
                                continue
                            
                            # MTT Alias Check
                            if org_w == 'mtt':
                                if 'maktabgacha' in text_clean or "bog'cha" in text_clean or "muassasasi" in text_clean:
                                    matches += 1
                                    continue
                                    
                            # MFY Alias Check - NEW
                            if org_w == 'mfy':
                                if 'mahalla' in text_clean or "fuqarolar" in text_clean or "yig'ini" in text_clean:
                                    matches += 1
                                    continue
                            
                            # Fuzzy check
                            if not org_w.isdigit(): 
                                 close = difflib.get_close_matches(org_w, text_words, n=1, cutoff=0.75)
                                 if close:
                                     matches += 1
                                     continue
                            
                            # Suffix check
                            found_root = False
                            for tx_w in text_words:
                                if len(tx_w) < 3: continue
                                if org_w.startswith(tx_w) or tx_w.startswith(org_w):
                                     matches += 1
                                     found_root = True
                                     break
                            if found_root: continue

                        # Calculate score based on percentage of words matched
                        ratio = matches / valid_word_count if valid_word_count > 0 else 0
                        
                        if ratio > 0.5: # At least 50% of words matched
                            name_score = int(ratio * 100)
                            
                            # Boost if key terms present
                            if "-son" in name_lower and "-son" in text_clean:
                                name_score += 20
                            
                            is_texnikum_in_text = "texnikum" in text_clean or "texnikuni" in text_clean
                            if is_texnikum_in_text and "kasb-hunar" in name_lower:
                                name_score += 30
                            
                            # Penalty for mismatching types
                            if "kasb-hunar" in name_lower and "kasb" not in text_clean and not is_texnikum_in_text:
                                name_score -= 50
                            if "umumiy" in name_lower and "umumiy" not in text_clean:
                                name_score -= 10
                        else:
                            name_score = 0
                
                # Combine scores (Person score + Name score) if person score was weak
                if current_score < name_score:
                    current_score = name_score

    
        if current_score > best_score and current_score > 40: # Threshold
            best_score = current_score
            best_match = name
            best_inn = inn_val
            best_person = person
            best_phone = phone

    if best_match:
        logger.info(f"Best Match: {best_match} (Score: {best_score})")
        return best_match, best_inn, best_person, best_phone


                            
    logger.info("No Organization Name found.")
    return None, None, None, None

def lookup_company_by_inn(inn):
    """Loads JSON and finds company name and person."""
    logger.debug(f"Looking up company by INN: {inn}")
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_path, "data.json")
        
        if not os.path.exists(json_path):
             logger.error(f"JSON file not found at {json_path}")
             return None

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            if str(item.get("inn")) == str(inn):
                # NEW STRUCTURE: 'm' for name, 'f' for person
                name = item.get("m", "Noma'lum")
                person = item.get("f", "")
                phone = item.get("t", "")
                logger.info(f"Match found: {name} | {person}")
                return {'name': name, 'person': person, 'phone': phone}
                
    except Exception as e:
        logger.error(f"JSON Lookup Error: {e}")
    return None

def search_organizations(query):
    """
    Searches for organizations by INN or Name (partial match).
    Returns a list of matching dictionaries: [{'inn': '...', 'name': '...', 'person': '...'}, ...]
    """
    query = str(query).strip().lower()
    if not query: return []
    
    logger.debug(f"Manual search query: {query}")
    
    results = []
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_path, "data.json")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Normalize query to uniformly handle cyrillic/latin
        query_norm = normalize_text(query).lower()
        
        # Split into parts (e.g. "50mtt" -> ["50", "mtt"], "oqdaryo 50 mtt" -> ["oqdaryo", "50", "mtt"])
        # We can use regex to separate numbers from letters. Apostrophes should be kept with letters.
        query_parts = re.findall(r'\d+|[a-z\']+', query_norm)
        
        if not query_parts:
            query_parts = [query_norm] # Fallback
            
        aliases = {
            "mtt": ["maktabgacha", "bog'cha", "dmtt", "mtt", "xalq ta'limi"],
            "maktab": ["maktab", "umumiy", "o'rta", "ta'lim"],
            "shifoxona": ["tibbiyot", "shifoxona", "poliklinika", "kasalxona", "dispanser"],
            "litsey": ["litsey", "akademik"],
            "mfy": ["mahalla", "fuqarolar", "yig'ini", "mfy"],
            "oshxona": ["oshxona", "kafe", "restoran", "ovqatlanish"]
        }
        
        for item in data:
            name = item.get("m", "")
            person = item.get("f", "")
            phone = item.get("t", "")
            inn = str(item.get("inn", ""))
            
            # 1. Exact INN match
            if query == inn:
                 results.append({'inn': inn, 'name': name, 'person': person, 'phone': phone})
                 continue
                 
            # 2. Substring INN match (only if query is all digits and at least 4 digits long)
            if query.isdigit() and len(query) >= 4 and query in inn:
                 results.append({'inn': inn, 'name': name, 'person': person, 'phone': phone})
                 continue
                 
            # Normalize names for robust searching
            name_norm = normalize_text(name).lower()
            person_norm = normalize_text(person).lower()
            
            # Simple exact substring on normalized text
            if query_norm in name_norm or query_norm in person_norm:
                results.append({'inn': inn, 'name': name, 'person': person, 'phone': phone})
                continue
                
            # If query is short number, strict word boundary match
            if query.isdigit() and len(query) < 4:
                if re.search(r'(^|\D)' + re.escape(query) + r'(\D|$)', name_norm):
                    results.append({'inn': inn, 'name': name, 'person': person, 'phone': phone})
                continue
                
            # Multi-part search (e.g. checks '50' AND 'mtt' simultaneously)
            match_all_parts = True
            for part in query_parts:
                part_match = False
                
                # strict number match
                if part.isdigit():
                    if re.search(r'(^|\D)' + re.escape(part) + r'(\D|$)', name_norm) or part in person_norm:
                        part_match = True
                else:
                    # check aliases
                    if part in aliases:
                        if any(alias_ext in name_norm for alias_ext in aliases[part]):
                            part_match = True
                    else:
                        if part in name_norm or part in person_norm:
                            part_match = True
                            
                if not part_match:
                    match_all_parts = False
                    break
                    
            if match_all_parts:
                results.append({'inn': inn, 'name': name, 'person': person, 'phone': phone})

    except Exception as e:
        logger.error(f"Search error: {e}")
        
    # Deduplicate results
    unique_results = []
    seen = set()
    for r in results:
        identifier = f"{r['inn']}_{r['name']}"
        if identifier not in seen:
            seen.add(identifier)
            unique_results.append(r)
            
    return unique_results[:20]

