#!/usr/bin/python
# -*- coding: utf8 -*-

from parse import *
import pymorphy2
import re

# class for processing lines of input file
class string_processor:
    def __init__ (self, filename):
        self.output_file = open(filename, 'w')

        self.template_number = 0

        self.lspl_template = lspl_template_maker()

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


class lspl_template_maker:
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
                                             'NPRO': 'Pn'
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
        result = self.get_template_as_string(self.total_template)

        self.total_template = []
        for type_name in self.part_of_speech_type_names:
            self.part_of_speech_types[type_name] = 0

        return result

    def get_template_as_string (self, template, is_option = False):
        result = ''
        for element in template:
            if element['is_list']:
                to_add = self.get_template_as_string(element['value'], element['is_optional'])
                if element['is_optional']:
                    to_add = ' [' + to_add[3:] + ']' # deleting first `|`
                if is_option:
                    result += ' |'
                result += to_add
            else:
                element_template = element['value']
                element_string = ' ' + element_template['type_name'] +\
                                str(element_template['type_number']) +\
                                '<'
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
                result += element_string

        return result

    def get_word_template (self, word, rebuild_pronoun = False, is_optional = False):
        if rebuild_pronoun:
            word_data = self.get_part_of_speech_data(word, 'Pn')

        else:
            word_data = self.get_part_of_speech_data(word)

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

    def get_part_of_speech_data (self, word, desirable_type = ''):
        possible_words = self.morph.parse(word)
        if desirable_type == '':
            word_parsed = possible_words[0]
        else:
            i = 0
            was_found = False
            for possible_word in possible_words:
                lspl_type = self.get_lspl_type(possible_word.tag.POS)
                if (lspl_type == desirable_type):
                    was_found = True
                    break
                i += 1

            if was_found:
                word_parsed = possible_words[i]
            else:
                word_parsed = possible_words[0]

        tag = word_parsed.tag

        normal_form = word_parsed.normal_form

        lspl_type = self.get_lspl_type(tag.POS)

        result = {'type_name': lspl_type, 'normal_form': normal_form}

        if word_parsed.tag.case:
            lspl_case = self.get_lspl_case(tag.case)
            result.update({'c': lspl_case})


        return result

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
    test_string = 'выступить с докладом (чего, о чем);' +\
    ' с [новой, следующей, имеющейся] гипотезой (чего, о чём);' +\
    '  с проповедью (о ком)'
    test_string2 = 'выявить пригодность (чего для чего)'

    # to_use_input_file = True
    to_use_input_file = False

    if to_use_input_file:
        input_file = open("dict_to_work_with.txt", 'r')
    else:
        input_file = [test_string, test_string2]

    line_processor = string_processor("generated_templates.txt")

    for line in input_file:
        line_processor.process(line)

    print ("Done.")
