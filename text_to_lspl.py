#!/usr/bin/python3
# -*- coding: utf8 -*-

import pymorphy2
import re

# class for processing lines of input file
class String_processor:
    def __init__ (self, filename):
        self.output_file = open(filename, 'w')

        self.template_number = 0

        self.lspl_template = Lspl_template_maker()

        word_pattern_str = '[^; ,\(\)\[\]\n]+'

        words_comma_separated_pattern_str = '[^\[\]\(\)\n]+'

        top_level_pattern_str = '\[' +\
         words_comma_separated_pattern_str +\
         '\]|\(' + words_comma_separated_pattern_str + '\)|' +\
          word_pattern_str

        extra_parts_pattern_str = ';[^;]+'

        self.top_level_pattern = re.compile(top_level_pattern_str)

        self.word_pattern = re.compile(word_pattern_str)

        self.extra_parts_pattern = re.compile(extra_parts_pattern_str)

    def process (self, string):
        if self.output_needed(string):
            separator_pos = string.find(';')
            if separator_pos == -1:
                main_part = string
            else:
                main_part = string[0 : separator_pos]

            # processing main part (before ';')
            self.write_template_of_elementary_string(main_part)

            # processing extra parts (after ';')
            top_level_words = self.word_pattern.findall(string) # to change to split
            # top_level_words = re.split(';', string)
            main_verb = top_level_words[0]

            extra_parts = self.extra_parts_pattern.findall(string)
            for fetched_extra_part in extra_parts: # fetched_extra_part has trailing ';'
                self.write_template_of_elementary_string(main_verb + ' ' + fetched_extra_part[1:])

        else:
            self.new_str()

    def write_template_of_elementary_string (self, string):
        top_level_parts = self.top_level_pattern.findall(string)
        for fetched_part in top_level_parts:
            if self.is_a_word(fetched_part):
                self.lspl_template.add_word_template(fetched_part)

            elif self.is_square_brackets_string(fetched_part):
                list_of_alternatives = re.split(', ', fetched_part[1 : -1])
                self.lspl_template.add_alternatives_from_list(list_of_alternatives)

            elif self.is_round_brackets_string(fetched_part):
                list_of_alternatives = re.split(', ', fetched_part[1 : -1])
                self.lspl_template.add_alternatives_from_list(list_of_alternatives, True)

        self.write_new_template(self.lspl_template.fetch_template_as_string())

    def output_needed (self, string):
        if string.find(' ') == -1:
            return False
        else:
            return True
            # Don`t know how to do it better. Will think about it.
            # verb_declaration = self.declaration_pattern.findall(string);
            # if verb_declaration == []:
            #     return True
            # else:
            #     return False

    def is_a_word (self, string):
        if (string[0] == '[' or string[0] == '('):
            return False
        else:
            return True

    def is_square_brackets_string(self, string):
        if (string[0] == '[' and string[-1] == ']'):
            return True
        else:
            return False

    def is_round_brackets_string(self, string):
        if (string[0] == '(' and string[-1] == ')'):
            return True
        else:
            return False

    def get_new_template_name (self):
        self.template_number += 1
        return 'P' + self.number_to_letters(self.template_number)
        # return 'P' + str(self.template_number)

    def number_to_letters (self, number):
        letters = ''
        while number > 0:
            last_digit = number % 26
            letters += chr(65+last_digit)
            number //= 26
        return letters

    def write_str (self, str):
        self.output_file.write(str)

    def new_str (self):
        self.output_file.write('\n')

    def write_new_template (self, template):
        self.write_str(self.get_new_template_name() + ' =')
        self.write_str(template)
        self.new_str()

    def __exit__ (self):
        self.output_file.close()


class Lspl_template_maker:
    def __init__ (self):
        self.morph = morph = pymorphy2.MorphAnalyzer()

        self.part_of_speech_type_names = ['W', 'N', 'A', 'V', 'Pa',
                                            'Ap', 'Pn', 'Av', 'Cn',
                                            'Pr', 'Pt', 'Int', 'Num']

        self.pymorphy_types_translator = {
                                             'INFN': 'V',
                                             'NOUN': 'N',
                                             'PREP': 'Pr',
                                             'ADJF': 'A',
                                             'PRTF': 'Pa',
                                             'ADVB': 'Av',
                                             'PRCL': 'Pt',
                                             'NPRO': 'Pn',
                                             'CONJ': 'Cn'
                                         }

        self.pymorphy_cases_translator = {
                                             'nomn': 'nom',
                                             'gent': 'gen',
                                             'datv': 'dat',
                                             'accs': 'acc',
                                             'ablt': 'ins',
                                             'loct': 'prep',
                                             # below are cases that are translated into best matching lspl cases
                                             'voct': 'nom',
                                             'gen2': 'gen',
                                             'acc2': 'acc',
                                             'loc2': 'prep'
                                         }

        self.part_of_speech_types = dict.fromkeys(self.part_of_speech_type_names, 0)

        self.total_template = []

    def add_word_template (self, word_to_create_template, rebuild_pronoun = False, is_optional = False):
        template = self.get_word_template(word_to_create_template, rebuild_pronoun, is_optional)
        self.total_template.append(template)

    def add_alternatives_from_list(self, alternatives_list, rebuild_pronoun = False):
        # this True can be changed to new argument value in the future
        result_template = {'is_list': True, 'is_optional': True}
        result_value = []
        for alternative in alternatives_list:
            words_of_alternative = re.split(' ', alternative)
            result_value.append(self.get_word_list_template(words_of_alternative, rebuild_pronoun, False))

        result_template.update({'value': result_value})
        self.total_template.append(result_template)

    def fetch_template_as_string (self):
        template_string_and_linear_word_list = self.get_template_string_and_linear_word_list(self.total_template, [])
        matching_str = self.get_matching_as_string (template_string_and_linear_word_list['linear_word_list'])
        result_str = template_string_and_linear_word_list['template_string'] + matching_str

        self.total_template = []
        for type_name in self.part_of_speech_type_names:
            self.part_of_speech_types[type_name] = 0

        return result_str

    def get_template_string_and_linear_word_list (self, template, linear_word_list, is_option = False):
        result_string = ''
        for element in template:
            if element['is_list']:
                recursive_data_getting = self.get_template_string_and_linear_word_list(element['value'],
                                                                        linear_word_list,
                                                                        element['is_optional'])
                str_to_add = recursive_data_getting['template_string']
                linear_word_list = recursive_data_getting['linear_word_list']
                if element['is_optional']:
                    str_to_add = ' [' + str_to_add[3:] + ']' # deleting first `|`
                if is_option:
                    result_string += ' |'
                result_string += str_to_add
            else:
                element_template = element['value']
                element_string = ' ' + element_template['type_name'] +\
                                str(element_template['type_number']) +\
                                '<'
                linear_word_list.append({'type_name': element_template['type_name'],
                                         'type_number': str(element_template['type_number'])})

                first_element_is_set = False
                if 'normal_form' in element_template:
                    element_string += element_template['normal_form']
                    first_element_is_set = True

                if 'c' in element_template:
                    if first_element_is_set:
                        element_string += ', '
                    else:
                        first_element_is_set = True
                    element_string += 'c=' + element_template['c']

                element_string += '>'
                if element['is_optional']:
                    element_string = '[' + element_string + ']'
                result_string += element_string

        return {'template_string': result_string, 'linear_word_list': linear_word_list}

    def get_matching_as_string (self, linear_word_list):
        result_string = ''
        matching_list = []
        one_matching_buffer = []
        for element in linear_word_list:
            if element['type_name'] == 'Pa' or element['type_name'] == 'A' or element['type_name'] == 'N' :
                one_matching_buffer.append(element)
                if element['type_name'] == 'N':
                    if not one_matching_buffer[0]['type_name'] == 'N':
                        matching_list.append(one_matching_buffer)
                    one_matching_buffer = []

        for one_matching in matching_list:
            first_element = one_matching.pop()
            result_string = first_element['type_name'] + first_element['type_number']
            for element in one_matching:
                result_string += '=' + element['type_name'] + element['type_number']

        if not result_string == '':
            result_string = '<' + result_string + '>'

        return result_string

    def get_word_template (self, word, rebuild_pronoun = False, is_optional = False):
        desirable_types = ['Pt', 'Pr', 'A', 'Pa', 'N', 'Av', 'V']
        desirable_cases = ['acc']
        if rebuild_pronoun:
            desirable_types.insert(0, 'Pn')
        word_data = self.get_part_of_speech_data(word, desirable_types, desirable_cases)

        if rebuild_pronoun and (word_data['type_name'] == 'Pn'):
            part_of_speech_number = self.new_part_of_speech_number('N')
            word_data.update({'type_name': 'N', 'type_number': part_of_speech_number})
            word_data.pop('normal_form')
        else:
            part_of_speech_number = self.new_part_of_speech_number(word_data['type_name'])
            word_data.update({'type_number': part_of_speech_number})

        result = {'is_list': False, 'is_optional': is_optional, 'value': word_data}
        return result

    def get_word_list_template (self, word_list, rebuild_pronoun = False, is_optional = False):
        result = {'is_list': True, 'is_optional': is_optional}
        value = []
        for word in word_list:
            value.append(self.get_word_template(word, rebuild_pronoun))
        result.update({'value': value})

        return result

    def new_part_of_speech_number (self, part_of_speech_type):
        self.part_of_speech_types[part_of_speech_type] += 1

        return self.part_of_speech_types[part_of_speech_type]

    def get_part_of_speech_data (self, word, desirable_types = [], desirable_cases = []):
        types_need_cases = ['N', 'Pn']
        possible_words = self.morph.parse(word)

        if desirable_types == []:
            word_parsed = possible_words[0]
        else:
            desirable_type_words = self.get_desirable_type_words(possible_words, desirable_types)
            if desirable_type_words == []:
                word_parsed = possible_words[0]
            else:
                if desirable_cases == []:
                    word_parsed = desirable_type_words[0]
                else:
                    desirable_case_words = self.get_desirable_case_words(desirable_type_words, desirable_cases)
                    if desirable_case_words == []:
                        word_parsed = desirable_type_words[0]
                    else:
                        word_parsed = desirable_case_words[0]

        tag = word_parsed.tag

        normal_form = word_parsed.normal_form

        lspl_type = self.get_lspl_type(tag.POS)

        result = {'type_name': lspl_type, 'normal_form': normal_form}

        # if word_parsed.tag.case: -- adding case to any part of speech having it
        if lspl_type in types_need_cases:
            lspl_case = self.get_lspl_case(tag.case)
            result.update({'c': lspl_case})

        return result

    def get_desirable_type_words(self, possible_words, desirable_types):
        words_with_desirable_types = dict.fromkeys(desirable_types, [])

        for possible_word in possible_words:
            lspl_type = self.get_lspl_type(possible_word.tag.POS)
            if (lspl_type in desirable_types):
                value = words_with_desirable_types[lspl_type].copy()
                value.append(possible_word)
                words_with_desirable_types.update({lspl_type: value})

        for desirable_type in desirable_types:
            if not words_with_desirable_types[desirable_type] == []:
                return words_with_desirable_types[desirable_type]
        return []

    def get_desirable_case_words(self, possible_words, desirable_cases, single_desired = True):
        prior_number = 'sing' if single_desired else 'plur'
        not_prior_number = 'plur' if single_desired else 'sing'
        words_with_desirable_cases = {}
        for key in desirable_cases:
            words_with_desirable_cases[key] = {'sing' : [], 'plur' : []}

        for possible_word in possible_words:
            lspl_case = self.get_lspl_case(possible_word.tag.case)
            if (lspl_case in desirable_cases):
                if 'sing' in possible_word.tag:
                    words_with_desirable_cases[lspl_case]['sing'].append(possible_word)
                else:
                    words_with_desirable_cases[lspl_case]['plur'].append(possible_word)

        for desirable_case in desirable_cases:
            if (words_with_desirable_cases[desirable_case][prior_number] != []):
                return words_with_desirable_cases[desirable_case][prior_number]
            if (words_with_desirable_cases[desirable_case][not_prior_number] != []):
                return words_with_desirable_cases[desirable_case][not_prior_number]

        return []

    def get_lspl_type(self, pymorphy_type):
        if pymorphy_type in self.pymorphy_types_translator:
            lspl_type = self.pymorphy_types_translator[pymorphy_type]
        else:
            # Part of speech type was not detected.
            # Consider it to be `word`
            lspl_type = 'W'

        return lspl_type

    def get_lspl_case(self, pymorphy_case):
        if pymorphy_case in self.pymorphy_cases_translator:
            lspl_case = self.pymorphy_cases_translator[pymorphy_case]
        else:
            lspl_case = ''

        return lspl_case

if __name__ == "__main__":
    print ("Text to lspl")
    print ("processing...")
    test_string1 = 'выступить с докладом (чего, о чем);' +\
    ' с [новой, следующей, имеющейся] гипотезой (чего, о чём);' +\
    '  с проповедью (о ком)'
    test_string2 = 'выявить пригодность (чего для чего)'
    test_string3 = 'вытекать из закона (чего, о чем)'
    test_string4 = 'выступить [горячим] сторонником (кого, чего)'

    # to_use_input_file = True
    to_use_input_file = False

    if to_use_input_file:
        input_file = open("dict_to_work_with.txt", 'r')
    else:
        input_file = [test_string1, test_string2, test_string3, test_string4]

    string_processor = String_processor("generated_templates.txt")

    for line in input_file:
        string_processor.process(line)

    print ("Done.")
