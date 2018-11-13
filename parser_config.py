config = {
    'types': {
        'fio': {
            'order_id': 1,
            'check_re': r'^[А-Я][а-яё\-]+\s+[А-Я][а-яё\-]+\s+[А-Я][а-яё\-]+$', # regexp for recognizing paragraph
            'not_re': r'^(Депутат Государственной Думы|Законотворчество|Депутат) ',             # extra regexp to not to match to
                                                                    # avoid incorrect recognitions 
            'also_contains': ['photo'], # list of extra content types which could
                                        # be found within current paragraph
            'next_items': ['position'], # actually not used
            'name': 'fio', 
            'do_not_replace_check_re': True, # leave data matched to 'check_re' regexp
                                             # otherwise matched data will be cropped 
        },
        'photo': {
            'order_id': 2,
            'name': 'photo',
            'is_image': True, # says that content type is image and we have to find
                              # <w:drawing> tags and save images from them
        },
        'position': {
            'order_id': 3,
            'check_re': r'^Депутат',
            'also_contains': [],
            'next_items': ['fraction'],
            'name': 'position',
            'do_not_replace_check_re': True,
        },
        'fraction': {
            'order_id': 4,
            'check_re': r'^Фракция',
            'also_contains': [],
            'next_items': ['bio'],
            'name': 'fraction',
            'do_not_replace_check_re': True,
        },
        'bio': {
            'order_id': 5,
            'check_re': r'^Биография:?\s*',
            'also_contains': [],
            'next_items': ['relations'],
            'name': 'bio',
        },
        'relations': {
            'order_id': 6,
            'name': 'relations',
            'check_re': r'^Аффиляция, связи:?\s*',
            'also_contains': ['family'],
        },
        'submitted': {
            'order_id': 7,
            'name': 'submitted',
            'check_re': r'^Внесенные законопроекты:?\s*',
        },
        'family': {
            'order_id': 8,
            'name': 'family',
            'text_re': r'(<a[^>]+>)?([А-Яа-яё\s]+)?(Женат|женат|замужем|Замужем).*?(?<!г)(\.|$)', # regexp for retrieving extra content 
                                                                             # data from  paragraph text
            'leave_also_contains_data': True, # don't touch data matched to text_re within original text,
                                              # otherwise data will be cropped
            'remove_links': True,

            # Examples:
            # Депутат женат с 2013 г., имеет дочь.
            # Женат, имеет двух сыновей.
            # <a href=\"link">Женат, двое детей</a> (9).
            # <a href=\"link://link.ru/abc-ssd">Женат, имеет двоих сыновей</a> (3).
        },
        'conclusion': {
            'order_id': 9,
            'name': 'conclusion',
            'check_re': r'Выводы:?\s*',
        },
        'lobby': {
            'order_id': 10,
            'name': 'lobby',
            'check_re': r'Группа лоббистов:?\s*',
            'list_of_strings': True, # export as list of strings,
                                     # otherwise content data will be exported like one string
            'remove_empty_items': True,
        }
    }
}