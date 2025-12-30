"""
Author: WANG Maonan
Description: 使用 OpenAI API 测试 VQA 数据，分为单图 VQA 和多图 VQA
"""
import os
import json
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI

class VQABenchmarkTest:
     """VQA Benchmark 测试类"""

     def __init__(self, api_key: str, base_url: str, model_name: str = "gpt-4o"):
          """
          初始化测试类
          
          Args:
               api_key: OpenAI API Key
               base_url: API Base URL
               model_name: 使用的模型名称
          """
          self.client = OpenAI(
               api_key=api_key, 
               base_url=base_url,
          )
          self.model_name = model_name
          
     def encode_image(self, image_path: str, max_size: int = 800, quality: int = 85) -> str:
          """
          将图片编码为 base64 格式，支持压缩
          
          Args:
               image_path: 图片路径
               max_size: 图片最大边长（像素），默认 800
               quality: JPEG 质量（1-100），默认 85
               
          Returns:
               base64 编码的图片字符串
          """
          # 打开图片
          img = Image.open(image_path)
          
          # 如果图片尺寸过大，进行缩放
          if max(img.size) > max_size:
               # 计算缩放比例
               ratio = max_size / max(img.size)
               new_size = tuple(int(dim * ratio) for dim in img.size)
               img = img.resize(new_size, Image.Resampling.LANCZOS)
          
          # 转换为 RGB 模式（如果需要）
          if img.mode in ('RGBA', 'LA', 'P'):
               # 创建白色背景
               background = Image.new('RGB', img.size, (255, 255, 255))
               if img.mode == 'P':
                    img = img.convert('RGBA')
               background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
               img = background
          elif img.mode != 'RGB':
               img = img.convert('RGB')
          
          # 保存到内存
          buffer = BytesIO()
          img.save(buffer, format='JPEG', quality=quality, optimize=True)
          buffer.seek(0)
          
          # 编码为 base64
          return base64.b64encode(buffer.read()).decode('utf-8')

     def test_single_image_vqa(self, vqa_item: dict, base_path: str) -> dict:
          """
          测试单图 VQA
          
          Args:
               vqa_item: VQA 数据项
               base_path: 图片基础路径
               
          Returns:
               包含预测结果和正确答案的字典
          """
          # 构建完整的图片路径
          image_path = os.path.join(base_path, vqa_item['image_path'])
          
          if not os.path.exists(image_path):
               print(f"⚠️  图片不存在: {image_path}")
               return None
          
          # 编码图片
          base64_image = self.encode_image(image_path)
          
          # 构建提示词
          question = vqa_item['question']
          options = vqa_item.get('options', {})
          
          # 如果有选项，添加到问题中
          if options:
               options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
               prompt = f"{question}\n\nOptions:\n{options_text}\n\nPlease only answer with the letter (A, B, C, etc.)."
          else:
               prompt = question

          # 调用 API
          try:
               response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                         {
                         "role": "user",
                         "content": [
                              {
                                   "type": "text",
                                   "text": prompt
                              },
                              {
                                   "type": "image_url",
                                   "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                   }
                              }
                         ]
                         }
                    ],
                    max_tokens=500
               )
               
               predicted_answer = response.choices[0].message.content.strip()
               
               return {
                    "question": question,
                    "predicted_answer": predicted_answer,
                    "correct_answer": vqa_item.get('correct_answer'),
                    "answer_text": vqa_item.get('answer'),
                    "options": options,
                    "image_path": image_path
               }
               
          except Exception as e:
               print(f"❌ API 调用失败: {e}")
               return None

     def test_multi_image_vqa(self, vqa_item: dict, base_path: str) -> dict:
          """
          测试多图 VQA
          
          Args:
               vqa_item: VQA 数据项
               base_path: 图片基础路径
               
          Returns:
               包含预测结果和正确答案的字典
          """
          # 构建消息内容（交替插入文本标签和图片）
          content = []
          images = vqa_item.get('images', [])
          question = vqa_item['question']
          options = vqa_item.get('options', {})
          
          # 构建提示词，明确说明图片顺序
          if options:
               options_text = "\n".join([f"{key}: {value}" for key, value in options.items()])
               prompt = f"{question}\n\n"
               prompt += f"The images are presented in order below (Image Index 0, Image Index 1, Image Index 2, ...).\n\n"
               prompt += f"Options:\n{options_text}\n\n"
               prompt += f"Please only answer with the letter (A, B, C, etc.) that best matches the images."
          else:
               prompt = f"{question}\n\nThe images are presented in order below (Image Index 0, Image Index 1, Image Index 2, ...)."
          
          content.append({"type": "text", "text": prompt})
          
          # 添加图片，每张图片前加上标签
          for idx, image_rel_path in enumerate(images):
               image_path = os.path.join(base_path, image_rel_path)
               
               if not os.path.exists(image_path):
                    print(f"⚠️  图片不存在: {image_path}")
                    continue
               
               # 添加图片索引标签
               content.append({
                    "type": "text",
                    "text": f"\n[Image Index {idx}]:"
               })
               
               # 编码并添加图片
               base64_image = self.encode_image(image_path)
               content.append({
                    "type": "image_url",
                    "image_url": {
                         "url": f"data:image/png;base64,{base64_image}"
                    }
               })

          # 调用 API
          try:
               response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                         {
                         "role": "user",
                         "content": content
                         }
                    ],
                    max_tokens=500
               )
               
               predicted_answer = response.choices[0].message.content.strip()
               
               return {
                    "question": question,
                    "predicted_answer": predicted_answer,
                    "correct_answer": vqa_item.get('correct_answer'),
                    "answer_text": vqa_item.get('answer'),
                    "options": options,
                    "images": images
               }
               
          except Exception as e:
               print(f"❌ API 调用失败: {e}")
               return None

     def test_cross_timestep_vqa(self, vqa_item: dict, base_path: str) -> dict:
          """
          测试跨时间步 VQA（问题部分包含图片，选项部分也包含图片）
          
          Args:
               vqa_item: VQA 数据项
               base_path: 图片基础路径
               
          Returns:
               包含预测结果和正确答案的字典
          """
          content = []
          question = vqa_item['question']
          options = vqa_item.get('options', {})
          question_type = vqa_item.get('question_type', '')
          
          # 构建问题提示
          image_type_map = {
               'bev_to_view': ('BEV (bird\'s-eye view)', 'bev_image'),
               'view_to_bev': ('directional view', 'view_image')
          }
          image_type, image_key = image_type_map.get(
               question_type, 
               ('reference', 'bev_image' if 'bev_image' in vqa_item else 'view_image')
          )
          
          # 添加问题和参考图片
          content.append({
               "type": "text",
               "text": f"{question}\n\nFirst, let me show you the {image_type} image:\n[Reference Image]:"
          })
          
          question_image_path = vqa_item.get(image_key, '')
          if question_image_path:
               self._add_image_to_content(content, os.path.join(base_path, question_image_path))
          
          # 添加选项说明
          content.append({
               "type": "text",
               "text": "\n\nNow, here are the candidate images with their corresponding options:"
          })
          
          # 添加选项图片（options 字典顺序与 option_images 列表顺序对应）
          option_images = vqa_item.get('option_images', [])
          for idx, (option_key, option_text) in enumerate(options.items()):
               if idx < len(option_images):
                    image_path = os.path.join(base_path, option_images[idx])
                    self._add_image_to_content(
                         content, 
                         image_path, 
                         label=f"\n[Option {option_key}] {option_text}:"
                    )
          
          # 添加最终提示
          content.append({
               "type": "text",
               "text": "\nPlease select the correct option (A, B, C, or D) that best matches the reference image. Only answer with the letter (A, B, C, or D)."
          })
          
          # 调用 API
          try:
               response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=500
               )
               
               return {
                    "question": question,
                    "question_type": question_type,
                    "predicted_answer": response.choices[0].message.content.strip(),
                    "correct_answer": vqa_item.get('correct_answer'),
                    "answer_text": vqa_item.get('answer_text'),
                    "options": options,
                    "question_image": question_image_path,
                    "option_images": option_images
               }
               
          except Exception as e:
               print(f"❌ API 调用失败: {e}")
               return None

     def _add_image_to_content(self, content: list, image_path: str, label: str = None) -> bool:
          """
          添加图片到 content，统一处理图片编码和错误
          
          Args:
               content: content 列表
               image_path: 图片完整路径
               label: 图片标签（可选）
               
          Returns:
               是否成功添加
          """
          if not os.path.exists(image_path):
               print(f"⚠️  图片不存在: {image_path}")
               return False
          
          try:
               if label:
                    content.append({"type": "text", "text": label})
               
               base64_image = self.encode_image(image_path, max_size=600, quality=80)
               content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
               })
               return True
          except Exception as e:
               print(f"⚠️  图片编码失败 {image_path}: {e}")
               return False

               
def simple_test():
     """简单测试：测试少量单图和多图VQA"""

     print("\n" + "="*60)
     print("VQA Benchmark - 简单测试")
     print("="*60 + "\n")

     # API 配置
     api_key = "sk-2LdDgrUtliwULsFaxUD46XfCqjfpbodbaMtiTZqhOAqtjKbN" # 国外
     #     api_key = "sk-hAMXwVPImjyy3kJcgWwtoLOoA9089cjFyriPtjJq4jTWyFep" # 国内
     base_url = "http://35.220.164.252:3888/v1"
     model_name = "gpt-5.1" # "qwen3-vl-8b-thinking" # "gpt-4o", "gemini-3-pro-preview"

     # 测试数据路径
     time_step = "177"
     vqa_data_path = f"/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/{time_step}/VQA/all_vqa.json"
     base_path = f"/mnt/petrelfs/wangmaonan/share_multimodal_traffic/multimodal_traffic/Beijing_Changjianglu/Beijing_Changjianglu_easy_fluctuating_commuter_barrier/"

     # 加载 VQA 数据
     print(f"📂 加载 VQA 数据: {vqa_data_path}")
     with open(vqa_data_path, 'r', encoding='utf-8') as f:
          vqa_data = json.load(f)
     print(f"✅ 加载成功，共 {len(vqa_data)} 条数据\n")

     # 创建测试实例
     tester = VQABenchmarkTest(api_key, base_url, model_name)

     # 测试单图 VQA
     print("📸 测试单图 VQA")
     print("-" * 60)
     single_image_data = [item for item in vqa_data if item.get('task') == 'Single Image']

     for idx, vqa_item in enumerate(single_image_data, 1):
          print(f"\n[{idx}] 问题: {vqa_item['question']}")
          print(f"    类别: {vqa_item.get('category', 'N/A')} - {vqa_item.get('subtask', 'N/A')}")
          print(f"    图片: {vqa_item.get('image_path', 'N/A')}")
     
          result = tester.test_single_image_vqa(vqa_item, base_path)
     
          if result:
               print(f"    完整路径: {result['image_path']}")
               print(f"    正确答案: {result['correct_answer']} - {result['answer_text']}")
               print(f"    模型回答: {result['predicted_answer']}")

     # 测试多图 VQA
     print("\n\n📸📸 测试多图 VQA")
     print("-" * 60)
     multi_image_data = [item for item in vqa_data if item.get('task') == 'Multi Image']

     for idx, vqa_item in enumerate(multi_image_data, 1):
          print(f"\n[{idx}] 问题: {vqa_item['question']}")
          print(f"    类别: {vqa_item.get('category', 'N/A')} - {vqa_item.get('subtask', 'N/A')}")
          print(f"    图片数量: {len(vqa_item.get('images', []))}")
     
          # 显示所有图片路径
          images = vqa_item.get('images', [])
          print(f"    图片列表:")
          for img_idx, img_path in enumerate(images):
               full_path = os.path.join(base_path, img_path)
               print(f"      [{img_idx}] {img_path}")
               print(f"          完整路径: {full_path}")
     
          result = tester.test_multi_image_vqa(vqa_item, base_path)
     
          if result:
               print(f"    正确答案: {result.get('correct_answer', 'N/A')} - {result['answer_text']}")
               print(f"    模型回答: {result['predicted_answer']}")

     # 测试跨时间步 VQA
     print("\n\n🔄📸 测试跨时间步 VQA (Cross-Timestep VQA)")
     print("-" * 60)
     cross_timestep_data = [item for item in vqa_data if item.get('task') == 'Cross-Timestep Multi Image']

     for idx, vqa_item in enumerate(cross_timestep_data, 1):
          print(f"\n[{idx}] 问题: {vqa_item['question']}")
          print(f"    类别: {vqa_item.get('category', 'N/A')} - {vqa_item.get('subtask', 'N/A')}")
          print(f"    问题类型: {vqa_item.get('question_type', 'N/A')}")
          
          # 显示问题图片
          question_type = vqa_item.get('question_type', '')
          if question_type == 'bev_to_view':
               question_image = vqa_item.get('bev_image', 'N/A')
               print(f"    问题图片 (BEV): {question_image}")
          elif question_type == 'view_to_bev':
               question_image = vqa_item.get('view_image', 'N/A')
               print(f"    问题图片 (View): {question_image}")
          
          # 显示选项图片
          option_images = vqa_item.get('option_images', [])
          print(f"    选项图片数量: {len(option_images)}")
          print(f"    选项图片列表:")
          for img_idx, img_path in enumerate(option_images):
               full_path = os.path.join(base_path, img_path)
               print(f"      [{img_idx}] {img_path}")
               print(f"          完整路径: {full_path}")
          
          result = tester.test_cross_timestep_vqa(vqa_item, base_path)
          
          if result:
               print(f"    正确答案: {result.get('correct_answer', 'N/A')} - {result.get('answer_text', 'N/A')}")
               print(f"    模型回答: {result['predicted_answer']}")

     print("\n" + "="*60)
     print("✅ 测试完成")
     print("="*60)


if __name__ == "__main__":
     simple_test()
