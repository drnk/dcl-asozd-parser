config = {
    'types': {
        'fio': {
            'order_id': 1,
            'check_re': r'[А-Я][а-я]+\s+[А-Я][а-я]+\s+[А-Я][а-я]+',
            'not_re': r'^Депутат Государственной Думы',
            'also_contains': ['photo'],
            'next_items': ['position'],
            'name': 'fio',
        },
        'photo': {
            'order_id': 2,
            'name': 'photo',
            'is_image': True,
        },
        'position': {
            'order_id': 3,
            'check_re': r'^Депутат',
            'also_contains': [],
            'next_items': ['fraction'],
            'name': 'position',
        },
        'fraction': {
            'order_id': 4,
            'check_re': r'^Фракция',
            'also_contains': [],
            'next_items': ['bio'],
            'name': 'fraction',
        },
        'bio': {
            'order_id': 5,
            'check_re': r'^Биография',
            'also_contains': [],
            'next_items': ['relations'],
            'name': 'bio',
        },
        'relations': {
            'order_id': 6,
            'name': 'relations',
            'check_re': r'^Аффиляция, связи:',
            'also_contains': ['family']
        },
        'submitted': {
            'order_id': 7,
            'name': 'submitted',
            'check_re': r'^Внесенные законопроекты:',
        },
        'family': {
            'order_id': 8,
            'name': 'family',
        },
        'conclusion': {
            'order_id': 9,
            'name': 'conclusion',
            'check_re': r'Выводы:',
        },
        'lobby': {
            'order_id': 10,
            'name': 'lobby',
            'check_re': r'Группа лоббистов:',
            'list_of_strings': True
        }
    }
}