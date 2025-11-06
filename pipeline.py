import re
from pathlib import Path
from typing import Dict, List, Union, Set

def count_characters(file_path: str):
    """ Считывает файл, считает количество символов до и после удаления непечатаемых символов """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return len(content)
    
    except FileNotFoundError:
        print("Файл не найден. Укажите корректный путь.")
    except Exception as e:
        print(f"Ошибка: {e}")
        

def get_all_files_by_types(
    directory: Union[str, Path],
    allowed_extensions: Set[str],
    recursive: bool = True
) -> List[Path]:
    """
    Рекурсивно находит все файлы с нужными расширениями.
    
    Args:
        directory: Путь к каталогу для поиска
        allowed_extensions: Множество разрешенных расширений (с точкой или без)
        recursive: Искать рекурсивно во всех подкаталогах
    
    Returns:
        Список путей ко всем найденным файлам
    """
    directory = Path(directory)
    
    # Нормализуем расширения (добавляем точку если нужно)
    normalized_extensions = {
        ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
        for ext in allowed_extensions
    }
    
    if recursive:
        iterator = directory.rglob('*')
    else:
        iterator = directory.glob('*')
    
    return [
        path for path in iterator
        if path.is_file() and path.suffix.lower() in normalized_extensions
    ]


def print_chars_stat(files: List[Path]):
    print("\n============ Количество знаков в каждом файле ============")
    for f in files:
        sf = str(f)
        print(count_characters(sf), sf)


def detect_ai_text_artifacts(file_path: Path, check_encoding: bool = True) -> Dict:
    """
    Проверяет файл на наличие невидимых символов и артефактов, характерных для текста от нейросетей.
    
    Args:
        file_path: Путь к файлу для проверки
        check_encoding: Проверять ли кодировку и BOM
    
    Returns:
        Словарь с результатами проверки
    """
    try:
        # Читаем файл в бинарном режиме для анализа сырых байтов
        with open(file_path, 'rb') as f:
            raw_content = f.read()
        
        # Пытаемся декодировать как текст
        try:
            # Сначала пробуем UTF-8
            content = raw_content.decode('utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            try:
                # Пробуем Windows-1251 (кириллица)
                content = raw_content.decode('cp1251')
                encoding = 'cp1251'
            except UnicodeDecodeError:
                # Если не получается, считаем бинарным файлом
                return {
                    'is_ai_likely': False,
                    'error': 'File is not a text file or uses unknown encoding',
                    'file_path': file_path
                }
        
        results = {
            'file_path': file_path,
            'encoding': encoding,
            'file_size': len(raw_content),
            'text_length': len(content),
            'checks': {},
            'is_ai_likely': False,
            'confidence_score': 0
        }
        
        # Словарь для хранения результатов проверок
        checks = {}
        
        # 1. Проверка на невидимые Unicode символы
        invisible_chars_found = []
        
        # Zero-width spaces, joiners, и другие невидимые символы
        zero_width_chars = {
            '\u200B': 'ZERO WIDTH SPACE',
            '\u200C': 'ZERO WIDTH NON-JOINER', 
            '\u200D': 'ZERO WIDTH JOINER',
            '\u2060': 'WORD JOINER',
            '\uFEFF': 'ZERO WIDTH NO-BREAK SPACE',
            '\u180E': 'MONGOLIAN VOWEL SEPARATOR',
            '\u200E': 'LEFT-TO-RIGHT MARK',
            '\u200F': 'RIGHT-TO-LEFT MARK',
            '\u202A': 'LEFT-TO-RIGHT EMBEDDING',
            '\u202B': 'RIGHT-TO-LEFT EMBEDDING',
            '\u202C': 'POP DIRECTIONAL FORMATTING',
            '\u202D': 'LEFT-TO-RIGHT OVERRIDE',
            '\u202E': 'RIGHT-TO-LEFT OVERRIDE'
        }
        
        for char, description in zero_width_chars.items():
            if char in content:
                count = content.count(char)
                invisible_chars_found.append({
                    'char': f'U+{ord(char):04X}',
                    'description': description,
                    'count': count
                })
        
        checks['invisible_unicode_chars'] = {
            'found': len(invisible_chars_found) > 0,
            'details': invisible_chars_found,
            'count': len(invisible_chars_found)
        }
        
        # 2. Проверка на BOM (Byte Order Mark)
        bom_detected = False
        if check_encoding and len(raw_content) >= 3:
            # UTF-8 BOM
            if raw_content[:3] == b'\xEF\xBB\xBF':
                bom_detected = True
            # UTF-16 BOM
            elif len(raw_content) >= 2 and raw_content[:2] in (b'\xFF\xFE', b'\xFE\xFF'):
                bom_detected = True
        
        checks['bom_present'] = {
            'found': bom_detected,
            'details': 'Byte Order Mark detected' if bom_detected else 'No BOM'
        }
        
        # 3. Проверка на нестандартные пробелы
        unusual_spaces = []
        unusual_space_chars = {
            '\u00A0': 'NO-BREAK SPACE',
            '\u2000': 'EN QUAD', 
            '\u2001': 'EM QUAD',
            '\u2002': 'EN SPACE',
            '\u2003': 'EM SPACE',
            '\u2004': 'THREE-PER-EM SPACE',
            '\u2005': 'FOUR-PER-EM SPACE',
            '\u2006': 'SIX-PER-EM SPACE',
            '\u2007': 'FIGURE SPACE',
            '\u2008': 'PUNCTUATION SPACE',
            '\u2009': 'THIN SPACE',
            '\u200A': 'HAIR SPACE',
            '\u202F': 'NARROW NO-BREAK SPACE',
            '\u205F': 'MEDIUM MATHEMATICAL SPACE',
            '\u3000': 'IDEOGRAPHIC SPACE'
        }
        
        for char, description in unusual_space_chars.items():
            if char in content:
                count = content.count(char)
                unusual_spaces.append({
                    'char': f'U+{ord(char):04X}',
                    'description': description,
                    'count': count
                })
        
        checks['unusual_spaces'] = {
            'found': len(unusual_spaces) > 0,
            'details': unusual_spaces,
            'count': len(unusual_spaces)
        }
        
        # 4. Проверка на контрольные символы
        control_chars = []
        for char in content:
            if ord(char) < 32 and char not in '\n\r\t':  # Исключаем обычные управляющие символы
                control_chars.append({
                    'char': f'U+{ord(char):02X}',
                    'description': f'CONTROL CHARACTER {ord(char):02X}'
                })
        
        checks['control_characters'] = {
            'found': len(control_chars) > 0,
            'details': control_chars[:10],  # Ограничиваем вывод
            'count': len(control_chars)
        }
        
        # 5. Проверка на шаблонные фразы нейросетей (опционально)
        ai_patterns = [
            r'как (искусственный интеллект|нейросеть|ИИ|AI)',
            r'(модель|нейросеть|ИИ) (обучен|обучалась)',
            r'сгенерирован[оа] (нейросетью|ИИ|искусственным интеллектом)',
            r'я (языковая модель|нейросеть|ИИ)',
            r'создан[оа] с помощью (GPT|ChatGPT|нейросети)',
            r'к сожалению,? (я|как ИИ)',
            r'не имею (личных|собственных)',
            r'моя (задача|функция)',
            r'основан[оа] на (обучении|тренировочных данных)'
        ]
        
        pattern_matches = []
        for pattern in ai_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                pattern_matches.extend(matches)
        
        checks['ai_patterns'] = {
            'found': len(pattern_matches) > 0,
            'details': list(set(pattern_matches))[:5],  # Уникальные матчи
            'count': len(pattern_matches)
        }
        
        results['checks'] = checks
        
        # Вычисляем общий счет уверенности
        confidence_score = 0
        
        if checks['invisible_unicode_chars']['found']:
            confidence_score += 30
        if checks['bom_present']['found']:
            confidence_score += 10  
        if checks['unusual_spaces']['found']:
            confidence_score += 20
        if checks['control_characters']['found']:
            confidence_score += 15
        if checks['ai_patterns']['found']:
            confidence_score += 25
        
        results['confidence_score'] = min(confidence_score, 100)
        results['is_ai_likely'] = confidence_score > 40
        
        return results
        
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e),
            'is_ai_likely': False,
            'confidence_score': 0
        }
        
        
def print_detected_ai_files(files: List[Path]):
    print("\n============ Проверка на непечатаемые символы и прочее галюны нейронки ============")
    is_correct = True
    for f in files:
        result = detect_ai_text_artifacts(f)
        if result.get('confidence_score', 0) > 0:
            is_correct = False
            print(result)
    if is_correct:
        print("ВСЕ ОК!")


if __name__ == "__main__":
    print("############### Начало Pipeline ###############")
    
    # 1. Получаем все файлы проекта
    files: List[Path] = get_all_files_by_types("LaTeX", {'.tex', '.bib'})

    # 2. Статистика по файлам
    print_chars_stat(files=files)
    print_detected_ai_files(files=files)