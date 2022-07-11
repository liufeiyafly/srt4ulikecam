# -*- coding:utf-8 -*-

import uuid
import json
import sys
import copy
import xmltodict
'''
主要功能：将srt字幕文件导入剪映。
    原理
    1. 往一个创建好的项目中的draft.json文件中导入srt字幕数据。

    参数只需要srt字幕文件即可。
'''

def read_json_template(filename):
    d=None
    try:
        with open(filename, 'r',encoding='utf-8') as f:
            d = json.load(f)
    except IOError as e:
        print(e)

    if len(d) > 0:
        return d
    else:
        raise Exception("the content of file `{}` is empty.\n".format(filename))

def read_srt_content(srt_filename):
    def srt_time_2_jianying_time(srt_time_formate):
        try:
            assert(len(srt_time_formate)==29)  # 必须是此样式的 '00:03:43,720 --> 00:03:45,340'
        except:
            print('发生错误，srt_time_formate此时是:{}'.format(srt_time_formate))
        start_and_end_time = srt_time_formate.split(' --> ')  # 结果为['00:03:43,720', '00:03:45,340']
        start_time = start_and_end_time[0].split(',')  # 结果为['00:03:43', '720']
        start_time_ms = colon_splited_time_2_ms(start_time[0]) + int(start_time[1])

        end_time = start_and_end_time[1].split(',')  # 结果为['00:03:45', '340']
        end_time_ms = colon_splited_time_2_ms(end_time[0]) + int(end_time[1])

        duration = end_time_ms - start_time_ms
        return (start_time_ms*1000, duration*1000)  # 剪映时间是微秒计的，所以要再乘1000

    def colon_splited_time_2_ms(colon_splited_time):  # 00:03:45 转为 1000(0*3600 + 3*60 + 45) = 225000
        hour_minute_second = colon_splited_time.split(':')
        assert(len(hour_minute_second) == 3)
        return 1000*(int(hour_minute_second[0])*60*60 +
            int(hour_minute_second[1])*60 +
            int(hour_minute_second[2]) )

    content=None
    try:
        with open(srt_filename, 'r',encoding='utf-8') as f:
            content = f.read()
    except IOError as e:
        print(e)
    new_list = []
    if content:
        all_subtitles_list = content.strip().split('\n\n')
        for element in all_subtitles_list:
            # '66\n00:02:28,990 --> 00:02:31,350\n have a ton of them' 转为 ['66', '00:02:28,990 --> 00:02:31,350', '字幕内容1', '字幕内容2']
            one_subtitle_info = element.split('\n')

            start_microsecond, duration = srt_time_2_jianying_time(one_subtitle_info[1])
            subtitle_content = '\n'.join(one_subtitle_info[2:])  # 字幕内容可能有多个，切片[2:] 就是当前时间片所有的字幕内容

            new_list.append([one_subtitle_info[0], start_microsecond, duration, subtitle_content])
    '''
        new_list内容为   [
                            [序号1, 起始微秒, 持续微秒, 字幕内容1],
                            [序号2, 起始微秒, 持续微秒, 字幕内容2]...
                        ]
    '''

    return new_list

def main(srt_file_path):
    RENDER_INDEX = 14000  # 剪映one_subtitle中该值从14000开始

    draft_content_file_path = './template/draft_content.json'
    material_animations_file_path = './template/material_animations.json'
    content_in_texts_file_path = './template/content_in_texts.json'
    all_subtitles_file_path = './template/all_subtitles.json'
    one_subtitle_file_path = './template/one_subtitle.json'
    # srt_file_path = ''

    draft_content = read_json_template(draft_content_file_path)  # 剪映draft_content.json文件
    material_animations = read_json_template(material_animations_file_path)  # 需要增加uuid
    content_in_texts = read_json_template(content_in_texts_file_path)  # 需要增加uuid, content
    all_subtitles = read_json_template(all_subtitles_file_path)  # 需要增加uuid,
    one_subtitle = read_json_template(one_subtitle_file_path)  # 需要增加uuid,extra_material_refs,material_id, duration,start

    texts = draft_content['materials']['texts']  # list
    tracks = draft_content['tracks']

    '''
    read_srt_content返回内容：[
                                [序号1, 起始微秒, 持续微秒, 字幕内容1],
                                [序号2, 起始微秒, 持续微秒, 字幕内容2]...
                            ]
    '''
    all_subtitles['id'] = str(uuid.uuid1())
    index = 0
    for element in read_srt_content(srt_file_path):
        # 往添加material_animations添加一个元素
        new_material_animations = copy.deepcopy(material_animations)
        new_material_animations['id'] = new_material_animations_uuid = str(uuid.uuid1())
        draft_content['materials']['material_animations'].append(new_material_animations)

        new_content_in_texts = copy.deepcopy(content_in_texts)
        new_content_in_texts['id'] = new_content_in_texts_uuid = str(uuid.uuid1())
        new_content_in_texts['content'] = element[3]

        texts.append(new_content_in_texts)

        new_one_subtitle = copy.deepcopy(one_subtitle)
        new_one_subtitle['id'] = str(uuid.uuid1())
        new_one_subtitle['material_id'] = new_content_in_texts_uuid
        new_one_subtitle['extra_material_refs'].append(new_material_animations_uuid)
        new_one_subtitle['target_timerange']['start'] = element[1]
        new_one_subtitle['target_timerange']['duration'] = element[2]
        new_one_subtitle['render_index'] = RENDER_INDEX + index
        index+=1

        all_subtitles['segments'].append(new_one_subtitle)

    tracks.append(all_subtitles)

    with open('draft_content_output.json','w', encoding='utf-8') as draft_content_finished_file:
        json.dump(draft_content, draft_content_finished_file)

if __name__=='__main__':
    print('** Start to Render... **\n')

    srt_file_path = sys.argv[1]
    main(srt_file_path)

    print('** Render Completely. **\n')