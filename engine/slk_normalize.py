# Puts protected SLK tables back into standard SYLK: line ends and real dimensions.
import re


RX_X = re.compile(r'X(\d+)')
RX_Y = re.compile(r'Y(\d+)')


def normalize(data_bytes):
    t = data_bytes.decode('utf-8', 'surrogateescape')
    t = t.replace('\r\r\n', '\r\n').replace('\r\n', '\n')
    line_list = t.split('\n')
    if line_list and line_list[-1] == '':
        line_list.pop()
    bs = [line for line in line_list if line.startswith('B;')]
    body = [line for line in line_list if not line.startswith('B;')]
    cur_x = cur_y = None
    max_x = max_y = 0
    for line in body:
        if not line.startswith('C;'):
            continue
        for c in line.split(';')[1:]:
            if c.startswith('X') and c[1:2].isdigit():
                cur_x = int(RX_X.match(c).group(1))
            elif c.startswith('Y') and c[1:2].isdigit():
                cur_y = int(RX_Y.match(c).group(1))
        if cur_x is not None:
            max_x = max(max_x, cur_x)
        if cur_y is not None:
            max_y = max(max_y, cur_y)
    if not body or not body[0].startswith('ID;'):
        raise ValueError('SLK without the ID record on the 1st line')
    b = 'B;X%d;Y%d;D0' % (max_x, max_y)
    output = [body[0], b] + body[1:]
    new = ('\r\n'.join(output) + '\r\n').encode('utf-8', 'surrogateescape')
    return new, {'b_before': bs, 'b_after': b, 'double_crlf': data_bytes.count(b'\r\r\n')}
