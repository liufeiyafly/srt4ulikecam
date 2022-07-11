# /usr/bin/env python
# -*- coding: utf-8 -*-

import xmltodict
import sys
import re
'''
需使用trados 和 srt 2个文件：
    将trados中的译文，插入到字幕中，生成新的srt文件。

    @Parameter 第一个参数为trados文件，第二个参数为srt文件。
'''
def trados_join_in_srt(trados_filename, srt_filename):
    # 打开trados文件
    trados_all_lines = None
    try:
        with open(trados_filename,'r',encoding='utf-8') as inputfile:
            trados_all_lines = inputfile.read()
    except IOError as e:
        print(e)

    # 打开srt文件
    srt_content=None
    try:
        with open(srt_filename, 'r',encoding='utf-8') as f:
            srt_content = f.read()
    except IOError as e:
        print(e)


    trados_list = []
    if trados_all_lines:
        d = xmltodict.parse(trados_all_lines)
        all_translation = d['xliff']['file']['body']['trans-unit'][1::2]
        for e in all_translation:
            try:
                translation = None
                translation = e.get('target').get('mrk').get('#text')
            except Exception as e:
                print(e)
            trados_list.append(translation if translation else '')  # 这里通过.get()方法获取的结果，只有两种类型：None或者str
    
    all_subtitles_list = []
    if srt_content:
        all_subtitles_list = srt_content.strip().split('\n\n')

    index = 0
    trados_list_length = len(trados_list)
    srt_new_list = [] # 需要生成新的srt文件，srt_new_list中存放即包含英文也包含中文的字符串。此时字幕中还没有\n\n分割符

    for element in all_subtitles_list:
        if index >= trados_list_length:
            break
        # '66\n00:02:28,990 --> 00:02:31,350\n have a ton of them' 转为 ['66', '00:02:28,990 --> 00:02:31,350', '字幕内容1', '字幕内容2']
        one_subtitle_info = element.split('\n')
        current_subtitle_lines_count = len(one_subtitle_info[2:])
        translations_list = trados_list[index:index+current_subtitle_lines_count]
        index = index + current_subtitle_lines_count

        new_translations_list_without_dot = []

        for one_trans in translations_list:
            if one_trans.count('.') != len(one_trans):
                new_translations_list_without_dot.append(one_trans)
        translations_string='，'.join(new_translations_list_without_dot)  # 以逗号分隔多行译文

        if translations_string != '':
            srt_new_list.append(one_subtitle_info[0] +'\n' +
                                one_subtitle_info[1] + '\n' +
                                '\n'.join(one_subtitle_info[2:]) + '\n' +
                                translations_string)
        else:
            srt_new_list.append(one_subtitle_info[0] +'\n' +
                                one_subtitle_info[1] + '\n' +
                                '\n'.join(one_subtitle_info[2:]))
    with open('{0}-output.srt'.format(srt_filename[:-4]), 'w', encoding='utf-8') as out_srt_file:
        out_srt_file.write('\n\n'.join(srt_new_list))

if __name__ == "__main__":
    print('** Start... **\n')
    trados_filename = sys.argv[1]
    srt_filename = sys.argv[2]

    try:
        assert(trados_filename[-9:] == '.sdlxliff')
    except:
        raise Exception('第一个文件必须是trados文件。\n')

    try:
        assert(srt_filename[-4:] == '.srt')
    except:
        raise Exception('第二个文件必须是trados文件。\n')
    trados_join_in_srt(trados_filename, srt_filename)
    print('** Done. **\n')
