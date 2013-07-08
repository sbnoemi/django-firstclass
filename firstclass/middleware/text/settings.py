from django.conf import settings
from django.utils.html import strip_tags
from firstclass.utils import call_or_format

def process_soup(soup):
    for selector, format in FIRSTCLASS_PLAINTEXT_RULES.iteritems():
        for el in reversed(soup.find_all(selector)):
            text = call_or_format(format, dict(el.attrs, text=getattr(el, 'text')), element=el)
            el.replaceWith(text)
    text = strip_tags(unicode(soup))
    return text

def anchor_to_text(attrs, **kwargs):
    text = attrs.get('href').strip()
    title = attrs.get('title', attrs.get('text', '')).strip()

    if text == title or not title:
        return text

    return '(%s) %s' % (title, text)

def image_to_text(attrs, **kwargs):
    text = attrs.get('src').strip()
    title = attrs.get('title', attrs.get('alt', '')).strip()

    if not title:
        return ''

    return '%s: %s' % (title, text)

def ul_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    items = ['\t* %s' % process_soup(item) for item in elem.find_all(['li'], recursive=False)]
    return '\n'.join(items)

def ol_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    items = [process_soup(item) for item in elem.find_all(['li'], recursive=False)]
    items = ['\t%d. %s' % (index, item) for index, item in enumerate(items)]
    return '\n'.join(items)
    
def h1_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    return '\n' + elem.text.upper() + ('\n' + len(elem.text) * '=')
    
    
def h2_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    return '\n' + elem.text + ('\n' + len(elem.text) * '=')
    
    
def h3_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    return '\n' + elem.text.upper() + ('\n' + len(elem.text) * '-')
    
def h4_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    return '\n' + elem.text + ('\n' + len(elem.text) * '-')
    
def h5_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    return '\n' + '=== ' + elem.text + ' ==='
    
def h6_to_text(attrs, **kwargs):
    elem = kwargs.get('element')
    if not elem:
        return ''
    return '\n' + '--- ' + elem.text + ' ---'
    
    

def table_to_text(attrs, **kwargs):
    table = kwargs.get('element')
    if not table:
        return ''
        
    thead = table.find_all('thead')
    tbody = table.find_all('tbody')
    tfoot = table.find_all('tfoot')
    
    rows = []
    
    if thead:
        for header in thead:
            rows.extend([(parse_row(row), True, False) for row in header.find_all('tr', recursive=False)])
        
    if tbody:
        for body in tbody:
            rows.extend([(parse_row(row), False, False) for row in body.find_all('tr', recursive=False)])
    else:
        rows.extend([(parse_row(row), False, False) for row in table.find_all('tr', recursive=False)])
        
    if tfoot:
        for footer in tfoot:
            rows.extend([(parse_row(row), False, True) for row in footer.find_all('tr', recursive=False)])
    
    text = make_table(rows)
    return text

def merge_cells(cells):
    new_cells = []
    colspan = 1
    for (text, name, cellspan) in cells:
        if not text.replace('&nbsp;', '').strip():
            colspan += cellspan
            continue
        new_cells.append((text, name, colspan))
    return new_cells

def parse_row(row_elem):
    cells = [(process_soup(elem), elem.name == 'th', elem.attrs.get('colspan', 1)) for elem in row_elem.find_all(['th', 'td'])]
#    cells = merge_cells(cells)
    return cells

# adapted from http://stackoverflow.com/a/12539081/394337
def make_table(grid):
    num_cols = max([len(row) for (row, is_head, is_foot) in grid])
    col_widths = [max(len(row[0][0]) for (row, row_head, row_foot) in grid) for i in range(num_cols)]
    rst = [table_div(None, col_widths, 0)]
    # 1 element, at index 0 at this point
    for ind, (row, is_header, is_footer) in enumerate(grid):
        # 1 + (2 * ind) elements at this point, with the last one at index 2 * ind
        cells = []
        cols_filled = 0
        cell_widths = []
        for (cell_text, is_header, colspan) in row:
            cell_width = sum(col_widths[cols_filled:cols_filled + int(colspan)]) + int(colspan) - 1
            cells.append(normalize_cell(cell_text, cell_width))
            cols_filled += int(colspan)
            cell_widths.append(cell_width)
        rst.append('| ' + ' | '.join(cells) + ' |')
        rst.append(table_div(row, col_widths, (is_header or is_footer), cell_widths=cell_widths))
        # 1 + (2 * (ind + 1)) elements at this point, with the last one at index 2 * (ind + 1)
        if is_footer:
            # replace previous divider with a "header" divider
            rst[ind * 2] = table_div(row, col_widths, True)
    return '\n'.join(rst)

def table_div(cells, col_widths, all_headers, cell_widths=None):
    if all_headers == 1:
        parts = [(col_width + 2) * '=' for col_width in col_widths]
    elif not cells:
        parts = [(col_width + 2) * '-' for col_width in col_widths]
    else:
        # num cells times single cell width plus a spacer for every colspan > 1
        parts = [(cell_widths[index] + 2) * '=' if is_header \
                    else (cell_widths[index] + 2) * '-' \
                    for index, (text, is_header, colspan) in enumerate(cells)]
    return '+' + '+'.join(parts) + '+'

def normalize_cell(cell_text, cell_width):
    return cell_text + (' ' * (cell_width - len(cell_text)))   

# Deprecated
FIRSTCLASS_TEXT_ANCHOR = getattr(settings, 'FIRSTCLASS_TEXT_ANCHOR', anchor_to_text)
FIRSTCLASS_TEXT_IMAGE = getattr(settings, 'FIRSTCLASS_TEXT_IMAGE', image_to_text)

FIRSTCLASS_PLAINTEXT_RULES = getattr(settings, 'FIRSTCLASS_PLAINTEXT_RULES', {
    'a': FIRSTCLASS_TEXT_ANCHOR,
    'img': FIRSTCLASS_TEXT_IMAGE,
    'table': table_to_text,
    'ul': ul_to_text,
    'ol': ol_to_text,
    'h1': h1_to_text,
    'h2': h2_to_text,
    'h3': h3_to_text,
    'h4': h4_to_text,
    'style': '',
})
