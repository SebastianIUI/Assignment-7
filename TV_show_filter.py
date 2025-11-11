# ----------------------------------------------------------------------
# Helper: split CSV line into fields respecting double quotes
# ----------------------------------------------------------------------
def _split_csv_line(line):
    fields = []
    cur = ''
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            if in_quotes and i + 1 < len(line) and line[i+1] == '"':
                cur += '"'
                i += 2
                continue
            in_quotes = not in_quotes
            i += 1
            continue
        if ch == ',' and not in_quotes:
            fields.append(cur)
            cur = ''
            i += 1
            continue
        cur += ch
        i += 1
    if cur.endswith('\n'):
        cur = cur[:-1]
    fields.append(cur)
    return fields

# ----------------------------------------------------------------------
# Helper: normalize a header name
# ----------------------------------------------------------------------
def _norm(s):
    return s.strip().lower().replace('_', ' ')

# ----------------------------------------------------------------------
# Improved date parser: handles "Present", "Ongoing", etc.
# ----------------------------------------------------------------------
def _parse_date(s):
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None

    # Remove surrounding quotes repeatedly if any
    while len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].strip()

    ls = s.lower().strip()

    # Treat these as "no end date"
    if ls in (
        'ongoing', 'present', 'current', 'still airing',
        'n/a', 'na', 'none', 'unknown', 'tbd'
    ):
        return None

    # ISO-like 2008-01-20 or 2008/01/20
    if '-' in s:
        parts = s.split('-')
        if len(parts) >= 3 and len(parts[0]) == 4:
            try:
                y = int(parts[0]); m = int(parts[1]); d = int(parts[2].split()[0])
                return (y, m, d)
            except Exception:
                return None
    if '/' in s:
        parts = s.split('/')
        if len(parts) >= 3:
            try:
                if len(parts[0]) == 4:
                    y = int(parts[0]); m = int(parts[1]); d = int(parts[2].split()[0])
                else:
                    m = int(parts[0]); d = int(parts[1]); y = int(parts[2].split()[0])
                return (y, m, d)
            except Exception:
                return None

    # Month name formats: e.g., January 3, 2020 or Jan 3 2020
    month_names = {
        'january':1,'jan':1,'february':2,'feb':2,'march':3,'mar':3,'april':4,'apr':4,
        'may':5,'june':6,'jun':6,'july':7,'jul':7,'august':8,'aug':8,'september':9,'sep':9,'sept':9,
        'october':10,'oct':10,'november':11,'nov':11,'december':12,'dec':12
    }
    parts = s.replace(',', ' ').split()
    if len(parts) >= 3:
        mname = parts[0].lower()
        if mname in month_names:
            try:
                m = month_names[mname]; d = int(parts[1]); y = int(parts[2])
                return (y, m, d)
            except Exception:
                return None

    # Plain 4-digit year
    if len(s) == 4 and s.isdigit():
        return (int(s), 1, 1)

    return None

# ----------------------------------------------------------------------
# Compare two (y,m,d) tuples. None counts as “after” any real date.
# ----------------------------------------------------------------------
def _date_less(a, b):
    if a is None or b is None:
        return False
    return a < b

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def shows_ended_before(input_csv_path, cutoff_date_str, output_csv_path):
    """Read `input_csv_path`, find shows whose end date is strictly before `cutoff_date_str`,
    and write `output_csv_path` with a single column `ShowName`.
    Returns number of shows written.
    """
    cutoff = _parse_date(cutoff_date_str)
    if cutoff is None:
        raise ValueError(f"Could not parse cutoff date: {cutoff_date_str!r}")

    try:
        f = open(input_csv_path, 'r', encoding='utf-8')
    except Exception:
        f = open(input_csv_path, 'r')

    header_line = None
    for line in f:
        if line.strip():
            header_line = line
            break
    if header_line is None:
        f.close()
        raise ValueError(f"Empty CSV file: {input_csv_path}")

    headers = _split_csv_line(header_line)
    name_idx = None
    end_idx = None
    for idx, h in enumerate(headers):
        hn = _norm(h)
        if name_idx is None and (hn == 'name' or 'title' in hn or 'show' in hn or hn == 'show name'):
            name_idx = idx
        if end_idx is None and ('end' in hn or 'finale' in hn or 'last' in hn):
            end_idx = idx

    if name_idx is None:
        name_idx = 0

    results = []
    for raw in f:
        if not raw.strip():
            continue
        fields = _split_csv_line(raw)
        if name_idx >= len(fields):
            continue
        name = fields[name_idx].strip()
        end_val = None
        if end_idx is not None and end_idx < len(fields):
            end_val = fields[end_idx].strip()
        end_date = _parse_date(end_val)
        if _date_less(end_date, cutoff):
            if name.startswith('"') and name.endswith('"') and len(name) >= 2:
                name = name[1:-1]
            results.append(name)
    f.close()

    try:
        of = open(output_csv_path, 'w', encoding='utf-8')
    except Exception:
        of = open(output_csv_path, 'w')
    of.write('ShowName\n')
    for nm in results:
        if '"' in nm:
            nm = nm.replace('"', '""')
        if ',' in nm or '\n' in nm or '"' in nm:
            of.write(f'"{nm}"\n')
        else:
            of.write(f'{nm}\n')
    of.close()
    return len(results)

from TV_show_filter import shows_ended_before

input_csv = r"C:\Users\sebas\Downloads\TV_show_data.csv"
cutoff = "2020-01-01"
output_csv = r"C:\Users\sebas\Downloads\ended_before_2020-01-01.csv"

count = shows_ended_before(input_csv, cutoff, output_csv)
print("Wrote", count, "shows to", output_csv)