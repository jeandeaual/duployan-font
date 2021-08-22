#!/usr/bin/env python3

# Copyright 2010-2019 Khaled Hosny <khaledhosny@eglug.org>
# Copyright 2018-2019 David Corbett
# Copyright 2020-2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import os
import re
import subprocess
import tempfile

import fontforge
import fontTools.misc.timeTools
import fontTools.ttLib
import fontTools.ttLib.tables.otBase
import fontTools.ttLib.ttFont

import duployan
import fonttools_patches

LEADING_ZEROS = re.compile('(?<= )0+')

def build_font(options, font):
    if os.environ.get('SOURCE_DATE_EPOCH') is None:
        os.environ['SOURCE_DATE_EPOCH'] = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ct'], encoding='utf-8').rstrip()
    font.selection.all()
    font.correctReferences()
    font.selection.none()
    flags = ['no-hints', 'omit-instructions', 'opentype']
    font.generate(options.output, flags=flags)

def generate_feature_string(font, lookup):
    with tempfile.NamedTemporaryFile() as fea_file:
        font.generateFeatureFile(fea_file.name, lookup)
        return fea_file.read().decode('utf-8')

def patch_fonttools():
    fontTools.ttLib.tables.otBase.BaseTTXConverter.compile = fonttools_patches.compile

def filter_map_name(name):
    if name.platformID != 3 or name.platEncID != 1:
        return None
    if isinstance(name.string, bytes):
        name.string = name.string.decode('utf-16be')
    if name.nameID == 5:
        name.string = LEADING_ZEROS.sub('', name.string)
    name.string = name.string.strip()
    return name

def set_subfamily_name(names, bold):
    for name in names:
        if name.nameID == 1:
            family_name = name.string
        elif name.nameID == 2:
            subfamily_name_record = name
            subfamily_name_record.string = 'Bold' if bold else 'Regular'
        elif name.nameID == 4:
            full_name_record = name
        elif name.nameID == 6:
            postscript_name_record = name
    full_name_record.string = family_name
    postscript_name_record.string = re.sub(r"[^!-$&-'*-.0-;=?-Z\\^-z|~]", '', family_name)
    if bold:
        full_name_record.string += f' {subfamily_name_record.string}'
        postscript_name_record.string += f'-{subfamily_name_record.string}'

def set_unique_id(names):
    for name in names:
        if name.nameID == 3:
            unique_id_record = name
        elif name.nameID == 4:
            full_name = name.string
        elif name.nameID == 5:
            version = name.string.removeprefix('Version ')
    git_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD'], encoding='utf-8').rstrip()
    unique_id_record.string = ';'.join([full_name, version, git_hash])

def add_meta(tt_font):
    meta = tt_font['meta'] = fontTools.ttLib.newTable('meta')
    meta.data['dlng'] = 'Dupl'
    meta.data['slng'] = 'Dupl'

def tweak_font(options, builder):
    with fontTools.ttLib.ttFont.TTFont(options.output, recalcBBoxes=False) as tt_font:
        # Remove the FontForge timestamp table.
        if 'FFTM' in tt_font:
            del tt_font['FFTM']

        # Merge all the lookups.
        font = builder.font
        lookups = font.gpos_lookups + font.gsub_lookups
        old_fea = ''.join(generate_feature_string(font, lookup) for lookup in lookups)
        for lookup in lookups:
            font.removeLookup(lookup)
        builder.merge_features(tt_font, old_fea)

        fontTools.feaLib.builder.addOpenTypeFeatures(
            tt_font,
            options.fea,
            tables=['OS/2', 'head', 'name'],
        )

        if options.bold:
            tt_font['OS/2'].usWeightClass = 700
            tt_font['OS/2'].fsSelection |= 1 << 5
            tt_font['OS/2'].fsSelection &= ~(1 << 0 | 1 << 6)
            tt_font['head'].macStyle |= 1 << 0
            for name in tt_font['name'].names:
                if name.nameID == 2:
                    subfamily_name_record = name
                    break
            subfamily_name_record.string = 'Bold'
        else:
            tt_font['OS/2'].fsSelection |= 1 << 6
            tt_font['OS/2'].fsSelection &= ~(1 << 0 | 1 << 5)

        tt_font['OS/2'].usWinAscent = max(tt_font['OS/2'].usWinAscent, tt_font['head'].yMax)
        tt_font['OS/2'].usWinDescent = max(tt_font['OS/2'].usWinDescent, -tt_font['head'].yMin)
        tt_font['OS/2'].sTypoAscender = tt_font['OS/2'].usWinAscent
        tt_font['OS/2'].sTypoDescender = -tt_font['OS/2'].usWinDescent
        tt_font['OS/2'].yStrikeoutPosition = duployan.STRIKEOUT_POSITION
        tt_font['OS/2'].yStrikeoutSize = builder.light_line
        tt_font['post'].underlinePosition = tt_font['OS/2'].sTypoDescender
        tt_font['post'].underlineThickness = builder.light_line
        tt_font['head'].created = fontTools.misc.timeTools.timestampFromString('Sat Apr  7 21:21:15 2018')
        tt_font['hhea'].ascender = tt_font['OS/2'].sTypoAscender
        tt_font['hhea'].descender = tt_font['OS/2'].sTypoDescender
        tt_font['hhea'].lineGap = tt_font['OS/2'].sTypoLineGap
        tt_font['name'].names = [*filter(None, map(filter_map_name, tt_font['name'].names))]
        set_subfamily_name(tt_font['name'].names, options.bold)
        set_unique_id(tt_font['name'].names)
        tt_font['CFF '].cff[0].Notice = next(name for name in tt_font['name'].names if name.nameID == 0).string

        add_meta(tt_font)

        tt_font.save(options.output)

def make_font(options):
    font = fontforge.font()
    font.familyname = 'Duployan'
    font.fontname = font.familyname
    font.fullname = font.familyname
    font.encoding = 'UnicodeFull'
    builder = duployan.Builder(font, options.bold)
    builder.augment()
    build_font(options, builder.font)
    patch_fonttools()
    tweak_font(options, builder)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Add Duployan glyphs to a font.')
    parser.add_argument('--bold', action='store_true', help='Make a bold font.')
    parser.add_argument('--fea', metavar='FILE', required=True, help='feature file to add')
    parser.add_argument('--output', metavar='FILE', required=True, help='output font')
    args = parser.parse_args()
    make_font(args)

