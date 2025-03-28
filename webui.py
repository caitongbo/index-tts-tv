import os
import shutil
import sys
import threading
import time
import re
from pydub import AudioSegment
import numpy as np
import soundfile as sf
import tempfile

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

import gradio as gr
# from utils.webui_utils import next_page, prev_page

from indextts.infer import IndexTTS
from tools.i18n.i18n import I18nAuto

i18n = I18nAuto(language="zh_CN")
MODE = 'local'
tts = IndexTTS(model_dir="checkpoints",cfg_path="checkpoints/config.yaml")

os.makedirs("outputs/tasks",exist_ok=True)
os.makedirs("prompts",exist_ok=True)

def infer(voice, text,output_path=None):
    if not output_path:
        output_path = os.path.join("outputs", f"spk_{int(time.time())}.wav")
    tts.infer(voice, text, output_path)
    return output_path

# def gen_single(prompt, text):
#     output_path = infer(prompt, text)
#     return gr.update(value=output_path,visible=True)

# def update_prompt_audio():
#     update_button = gr.update(interactive=True)
#     return update_button

def split_sentences(text):
    """将文本分割成句子"""
    # 使用标点符号作为分隔符
    # separators = r'[，。！？；]'
    separators = r'[。！？；]'

    sentences = re.split(separators, text)
    # 过滤空字符串
    return [s.strip() for s in sentences if s.strip()]

def save_audio_data(sample_rate, audio_data):
    """将音频数据保存为临时文件"""
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        # 将数组数据保存为WAV文件
        sf.write(temp_file.name, audio_data, sample_rate)
        return temp_file.name
    except Exception as e:
        print(f"保存音频数据时出错: {str(e)}")
        return None

def merge_audio_files(audio_files, output_path):
    """合并多个音频文件"""
    try:
        print(f"开始合并音频文件，输入数据数量: {len(audio_files)}")
        combined = AudioSegment.empty()
        temp_files = []
        
        for i, audio_file in enumerate(audio_files):
            print(f"处理第 {i+1} 个音频数据")
            try:
                if isinstance(audio_file, tuple) and len(audio_file) == 2:
                    # 处理 (sample_rate, audio_data) 格式
                    sample_rate, audio_data = audio_file
                    temp_path = save_audio_data(sample_rate, audio_data)
                    if temp_path:
                        temp_files.append(temp_path)
                        sound = AudioSegment.from_wav(temp_path)
                        combined += sound
                elif isinstance(audio_file, str):
                    # 处理文件路径格式
                    sound = AudioSegment.from_wav(audio_file)
                    combined += sound
                else:
                    print(f"警告: 无效的音频数据格式 - {type(audio_file)}")
            except Exception as e:
                print(f"处理第 {i+1} 个音频时出错: {str(e)}")
                continue
        
        if len(combined) == 0:
            print("警告: 没有有效的音频数据被合并")
            return None
            
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        print(f"保存合并后的音频到: {output_path}")
        combined.export(output_path, format="wav")
        
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
                
        return output_path
    except Exception as e:
        print(f"合并音频文件时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# def gen_split_sentences(text):
#     """生成分句后的文本框和音频组件"""
#     sentences = split_sentences(text)
#     text_boxes = []
#     audio_outputs = []
#     gen_buttons = []
    
#     for i, sentence in enumerate(sentences):
#         text_boxes.append(gr.Textbox(value=sentence, label=f"句子 {i+1}"))
#         audio_outputs.append(gr.Audio(label=f"句子 {i+1} 音频"))
#         gen_buttons.append(gr.Button(f"生成句子 {i+1}"))
    
#     merge_btn = gr.Button("合并所有音频", visible=len(sentences) > 1)
#     final_audio = gr.Audio(label="最终合并音频")
    
#     return text_boxes + gen_buttons + audio_outputs + [merge_btn, final_audio]

def merge_generated_audios(*audio_components):
    """合并已生成的音频"""
    try:
        print("开始合并音频处理...")
        print(f"收到的音频组件数量: {len(audio_components)}")
        
        # 过滤出有效的音频数据
        valid_audio_data = []
        for i, comp in enumerate(audio_components):
            print(f"检查第 {i+1} 个音频组件: {comp}")
            if comp is not None:
                if isinstance(comp, str) and os.path.exists(comp):
                    valid_audio_data.append(comp)
                elif isinstance(comp, tuple) and len(comp) == 2:
                    # 处理 (sample_rate, array) 格式的音频数据
                    valid_audio_data.append(comp)
        
        print(f"找到 {len(valid_audio_data)} 个有效音频数据")
        
        if not valid_audio_data:
            print("没有找到可合并的音频数据")
            return gr.update(visible=False)
        
        output_path = os.path.join("outputs", f"merged_{int(time.time())}.wav")
        result_path = merge_audio_files(valid_audio_data, output_path)
        
        if result_path and os.path.exists(result_path):
            print(f"成功生成合并音频: {result_path}")
            return gr.update(value=result_path, visible=True)
        else:
            print("合并音频失败")
            return gr.update(visible=False)
            
    except Exception as e:
        print(f"合并音频时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return gr.update(visible=False)

def generate_single_audio(prompt_audio, text):
    """生成单个句子的音频"""
    try:
        if not prompt_audio or not text:
            print("参考音频或文本为空")
            return None
            
        output_path = infer(prompt_audio, text)
        return output_path
        
    except Exception as e:
        print(f"生成音频时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def continue_to_next_audio(current_audio_out, *all_audio_components):
    """当前音频播放结束后，自动播放下一条音频"""
    try:
        print("开始处理自动播放...")
        print(f"当前音频数据: {current_audio_out}")
        print(f"所有音频组件数量: {len(all_audio_components)}")
        
        # 找到当前音频组件的索引
        current_idx = -1
        for i, comp in enumerate(all_audio_components):
            if comp is not None and isinstance(comp, tuple) and len(comp) == 2:
                # 比较采样率和数组是否相同
                if (comp[0] == current_audio_out[0] and 
                    np.array_equal(comp[1], current_audio_out[1])):
                    current_idx = i
                    break
        
        print(f"找到当前音频索引: {current_idx}")
        
        if current_idx == -1:
            print("未找到当前音频组件，尝试查找第一个有效音频")
            # 如果找不到当前音频，从头开始播放
            for i, comp in enumerate(all_audio_components):
                if comp is not None and isinstance(comp, tuple) and len(comp) == 2:
                    current_idx = i - 1  # 设置为第一个有效音频的前一个位置
                    break
        
        next_idx = current_idx + 1
        print(f"当前音频索引: {current_idx}, 下一个索引: {next_idx}")
        
        # 检查是否有下一个有效的音频
        while next_idx < len(all_audio_components):
            next_audio = all_audio_components[next_idx]
            if next_audio is not None and isinstance(next_audio, tuple) and len(next_audio) == 2:
                print(f"找到下一个有效音频，索引: {next_idx}")
                # 更新所有音频组件
                updates = []
                for i, comp in enumerate(all_audio_components):
                    if i == next_idx:
                        # 将下一个音频设置为自动播放
                        updates.append(gr.update(visible=True, value=next_audio, autoplay=True))
                    else:
                        # 其他音频组件保持原样但不自动播放
                        updates.append(gr.update(visible=True, value=comp if comp is not None else None, autoplay=False))
                return updates
            next_idx += 1
        
        print("没有找到下一个有效音频，保持当前状态")
        # 如果没有下一个有效音频，保持所有组件当前状态
        return [gr.update(visible=True, value=comp if comp is not None else None) for comp in all_audio_components]
            
    except Exception as e:
        print(f"自动播放下一个音频时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return [gr.update(visible=True)] * len(all_audio_components)

with gr.Blocks() as demo:
    mutex = threading.Lock()
    state = gr.State([])
    
    with gr.Tab("音频生成"):
        with gr.Row(equal_height=True):
            input_text = gr.Textbox(
                label="请输入目标文本",
                lines=2,
                max_lines=5,
                scale=2,
                show_copy_button=True
            )
            prompt_audio = gr.Audio(
                label="请上传参考音频",
                sources=["upload","microphone"],
                type="filepath",
                scale=2
            )
            split_button = gr.Button(
                "分句生成",
                scale=1,
                min_width=100
            )
        
        dynamic_container = gr.Column()
        with dynamic_container:
            output_box = gr.Column(visible=False)
            merge_row = gr.Row(visible=False)
            with merge_row:
                merge_btn = gr.Button("合并所有音频", scale=1)
                final_audio = gr.Audio(
                    label="最终合并音频", 
                    scale=2,
                    interactive=False,
                    sources=None
                )

            # 预先创建一些可重用的组件
            sentence_rows = []
            max_sentences = 20  # 设置一个合理的最大句子数
            
            for i in range(max_sentences):
                with gr.Row(visible=False, equal_height=True) as row:
                    text_box = gr.Textbox(
                        label=f"句子 {i+1}",
                        scale=4,  # 增加文本框的比例
                        min_width=200,
                        lines=2,
                        max_lines=5,
                        show_copy_button=True
                    )
                    audio_out = gr.Audio(
                        label=f"句子 {i+1} 音频",
                        scale=4,  # 增加音频组件的比例
                        interactive=False,
                        sources=None
                    )
                    gen_btn = gr.Button(
                        f"生成句子 {i+1}",
                        scale=1,  # 保持按钮比例较小
                        min_width=100
                    )
                    # 在 Blocks 上下文中绑定事件
                    gen_btn.click(
                        fn=generate_single_audio,
                        inputs=[prompt_audio, text_box],
                        outputs=[audio_out]
                    )
                    sentence_rows.append((row, text_box, audio_out, gen_btn))

            # 为每个音频组件添加 stop 事件，实现自动播放下一条
            for i, (_, _, audio_out, _) in enumerate(sentence_rows[:max_sentences]):
                audio_out.stop(
                    fn=continue_to_next_audio,
                    inputs=[audio_out] + [comp[2] for comp in sentence_rows[:max_sentences]],  # 传入当前音频组件和所有音频组件
                    outputs=[comp[2] for comp in sentence_rows[:max_sentences]]  # 更新所有音频组件
                )

        def create_and_generate_all(text, prompt_audio):
            """分句并生成所有音频"""
            try:
                if not prompt_audio or not text:
                    print("参考音频或文本为空")
                    return [gr.update(visible=False)] * (len(sentence_rows) * 3 + 2)
                
                sentences = split_sentences(text)
                if not sentences:
                    print("没有找到有效的句子")
                    return [gr.update(visible=False)] * (len(sentence_rows) * 3 + 2)
                
                # 限制句子数量
                sentences = sentences[:max_sentences]
                print(f"处理 {len(sentences)} 个句子")
                
                updates = []
                audio_paths = []  # 存储生成的音频路径
                
                # 更新组件可见性和内容，并生成音频
                for i, sentence in enumerate(sentences):
                    row, text_box, audio_out, _ = sentence_rows[i]
                    # 生成音频
                    audio_path = generate_single_audio(prompt_audio, sentence)
                    if audio_path and os.path.exists(audio_path):
                        audio_paths.append(audio_path)
                        print(f"生成句子 {i+1} 音频: {audio_path}")
                        
                        updates.extend([
                            gr.update(visible=True),  # row
                            gr.update(value=sentence, visible=True),  # text_box
                            gr.update(value=audio_path, visible=True)  # audio_out
                        ])
                    else:
                        print(f"句子 {i+1} 音频生成失败")
                        updates.extend([
                            gr.update(visible=True),  # row
                            gr.update(value=sentence, visible=True),  # text_box
                            gr.update(visible=True)  # audio_out
                        ])
                
                # 隐藏未使用的行
                for i in range(len(sentences), max_sentences):
                    row, text_box, audio_out, _ = sentence_rows[i]
                    updates.extend([
                        gr.update(visible=False),  # row
                        gr.update(visible=False),  # text_box
                        gr.update(visible=False)  # audio_out
                    ])
                
                # 更新合并按钮和输出框的可见性（移除顺序播放行）
                updates.extend([
                    gr.update(visible=True),  # output_box
                    gr.update(visible=len(sentences) > 1),  # merge_row
                ])
                
                return updates
                
            except Exception as e:
                print(f"生成音频时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                return [gr.update(visible=False)] * (len(sentence_rows) * 3 + 2)  # 减少一个更新

        # 修改分句按钮文本和事件绑定
        split_button.value = "一键生成"  # 更新按钮文本
        
        split_button.click(
            fn=create_and_generate_all,
            inputs=[input_text, prompt_audio],
            outputs=[
                *[component for row in sentence_rows for component in row[:-1]],  # 所有行的组件（除了按钮）
                output_box,
                merge_row,
            ]
        )

        # 修改合并按钮的事件绑定
        merge_btn.click(
            fn=merge_generated_audios,
            inputs=[comp[2] for comp in sentence_rows[:max_sentences]],  # 获取所有音频输出组件
            outputs=[final_audio]
        )

if __name__ == "__main__":
    demo.queue(20)
    demo.launch(server_name="0.0.0.0")

    # v1 v2 v3 v4