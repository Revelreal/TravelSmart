# MainProject/app/services/mongo_file_service.py
import base64
import io
from typing import Optional, Tuple
from PIL import Image
from MainProject.dbhelper.MONGOHelper import MongoHelper


class MongoFileService:
    """基于MongoDB的文件服务"""

    def __init__(self):
        try:
            # 使用MongoHelper实例
            self.mongo = MongoHelper()
            self.collection_name = "user_files"
            self.max_file_size = 5 * 1024 * 1024  # 5MB
            self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

            # 初始化集合和索引
            self._init_collection()
            # 确保默认头像存在
            self._ensure_default_avatar()

            print("MongoDB文件服务初始化成功")
        except Exception as e:
            print(f"MongoDB文件服务初始化失败: {e}")
            raise

    def _init_collection(self):
        """初始化集合和索引"""
        try:
            # 创建集合并建立索引
            indexes = [
                "file_key",  # 文件键索引
                "user_id",  # 用户ID索引
                "file_type",  # 文件类型索引
                [("user_id", 1), ("file_type", 1)]  # 复合索引
            ]
            self.mongo.create_collection_with_indexes(self.collection_name, indexes)
            print("文件服务集合初始化完成")
        except Exception as e:
            print(f"初始化文件服务集合失败: {e}")
            raise

    def _ensure_default_avatar(self):
        """确保默认头像存在"""
        try:
            # 检查是否已存在默认头像
            existing = self.mongo.find_one(
                self.collection_name,
                {"file_key": "default_avatar"}
            )

            if not existing:
                print("创建默认头像...")
                # 创建一个简单的默认头像
                default_avatar_data = self._create_default_avatar_data()

                result = self.mongo.insert_one(self.collection_name, {
                    "file_key": "default_avatar",
                    "file_type": "avatar",
                    "mime_type": "image/png",
                    "file_data": default_avatar_data,
                    "created_at": self.mongo.get_current_time()
                })

                if result:
                    print("创建默认头像成功")
                else:
                    print("创建默认头像失败")
            else:
                print("默认头像已存在")
        except Exception as e:
            print(f"创建默认头像失败: {e}")
            import traceback
            traceback.print_exc()

    def _create_default_avatar_data(self) -> str:
        """创建默认头像的Base64数据"""
        # 创建一个100x100的灰色头像
        img = Image.new('RGB', (100, 100), color='#f0f0f0')

        # 可以在这里添加一些简单的图形，比如一个圆形或者文字
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)

        # 画一个简单的圆形作为默认头像
        draw.ellipse([20, 20, 80, 80], fill='#cccccc', outline='#999999', width=2)

        # 转换为Base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_data = buffer.getvalue()
        return base64.b64encode(img_data).decode('utf-8')

    def _read_file_data(self, file_input) -> Optional[bytes]:
        """读取文件数据 - 改进版"""
        try:
            print(f"尝试读取文件: {file_input}, 类型: {type(file_input)}")

            # 如果是文件对象
            if hasattr(file_input, 'read'):
                print("从文件对象读取数据")
                file_input.seek(0)  # 确保从文件开始读取
                data = file_input.read()
                print(f"从文件对象读取了 {len(data)} 字节")
                return data

            # 如果是文件路径字符串
            if isinstance(file_input, str):
                print(f"从文件路径读取数据: {file_input}")
                import os
                if os.path.exists(file_input):
                    with open(file_input, 'rb') as f:
                        data = f.read()
                        print(f"从文件路径读取了 {len(data)} 字节")
                        return data
                else:
                    print(f"文件不存在: {file_input}")
                    return None

            # 如果是 Gradio 的 NamedString 或类似对象
            if hasattr(file_input, 'name') and hasattr(file_input, '__fspath__'):
                print("从 Gradio 文件对象读取数据")
                file_path = str(file_input)
                import os
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        data = f.read()
                        print(f"从 Gradio 文件对象读取了 {len(data)} 字节")
                        return data

            # 如果有 name 属性，尝试作为路径
            if hasattr(file_input, 'name'):
                print(f"尝试使用 name 属性作为路径: {file_input.name}")
                import os
                if os.path.exists(file_input.name):
                    with open(file_input.name, 'rb') as f:
                        data = f.read()
                        print(f"从 name 属性路径读取了 {len(data)} 字节")
                        return data

            print(f"无法处理的文件类型: {type(file_input)}")
            print(f"文件对象属性: {dir(file_input)}")
            return None

        except Exception as e:
            print(f"读取文件数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def save_avatar(self, user_id: int, uploaded_file) -> Tuple[bool, str, Optional[str]]:
        """保存用户头像到MongoDB - 改进版"""
        try:
            print(f"开始保存头像，用户ID: {user_id}")
            print(f"上传文件类型: {type(uploaded_file)}")
            print(f"上传文件内容: {uploaded_file}")

            # 处理文件输入 - 改进版
            if uploaded_file is None:
                return False, "没有选择文件", None

            file_obj = None

            # 如果是列表，取第一个文件
            if isinstance(uploaded_file, list):
                if len(uploaded_file) == 0:
                    return False, "文件列表为空", None
                file_obj = uploaded_file[0]
                print(f"从列表中取得文件: {file_obj}")
            else:
                file_obj = uploaded_file
                print(f"直接使用文件对象: {file_obj}")

            # 检查文件对象
            if not file_obj:
                return False, "无效的文件对象", None

            # 获取文件路径或名称
            file_path = None
            if hasattr(file_obj, 'name'):
                file_path = file_obj.name
                print(f"文件名: {file_path}")
            elif isinstance(file_obj, str):
                file_path = file_obj
                print(f"文件路径: {file_path}")
            else:
                # 尝试转换为字符串
                try:
                    file_path = str(file_obj)
                    print(f"转换后的文件路径: {file_path}")
                except:
                    return False, "无法获取文件路径", None

            # 验证文件类型
            from pathlib import Path
            try:
                ext = Path(file_path).suffix.lower()
                print(f"文件扩展名: {ext}")
            except:
                return False, "无法获取文件扩展名", None

            if ext not in self.allowed_extensions:
                return False, f"不支持的文件类型: {ext}，支持的类型: {', '.join(self.allowed_extensions)}", None

            # 读取文件数据
            file_data = self._read_file_data(file_obj)
            if not file_data:
                return False, "无法读取文件数据", None

            print(f"文件数据大小: {len(file_data)} 字节")

            # 验证文件大小
            if len(file_data) > self.max_file_size:
                return False, f"文件大小超过限制（{self.max_file_size // (1024 * 1024)}MB）", None

            # 压缩图片
            try:
                compressed_data = self._compress_image(file_data, ext)
                print(f"压缩后数据大小: {len(compressed_data)} 字节")
            except Exception as e:
                print(f"图片压缩失败: {e}")
                compressed_data = file_data  # 使用原始数据

            # 转换为Base64
            base64_data = base64.b64encode(compressed_data).decode('utf-8')

            # 生成文件键
            file_key = f"avatar_user_{user_id}"

            # 删除旧头像
            try:
                self._delete_old_avatar(user_id)
            except Exception as e:
                print(f"删除旧头像失败: {e}")

            # 保存到MongoDB
            file_doc = {
                "file_key": file_key,
                "user_id": user_id,
                "file_type": "avatar",
                "mime_type": self._get_mime_type(ext),
                "file_data": base64_data,
                "original_filename": Path(file_path).name,
                "file_size": len(compressed_data),
                "created_at": self.mongo.get_current_time()
            }

            print(f"准备保存文档: {file_key}")
            result = self.mongo.insert_one(self.collection_name, file_doc)
            print(f"MongoDB插入结果: {result}")

            if result:
                print(f"头像保存成功，文件键: {file_key}")
                return True, "头像上传成功", file_key
            else:
                print("保存到数据库失败")
                return False, "保存到数据库失败", None

        except Exception as e:
            print(f"保存头像错误: {e}")
            import traceback
            traceback.print_exc()
            return False, f"保存失败: {str(e)}", None

    def _compress_image(self, image_data: bytes, ext: str) -> bytes:
        """压缩图片"""
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_data))

            # 转换为RGB（如果是RGBA）
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # 调整大小（最大300x300）
            max_size = (300, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 保存为JPEG以减小文件大小
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()

        except Exception as e:
            print(f"压缩图片失败: {e}")
            return image_data  # 返回原始数据

    def _get_mime_type(self, ext: str) -> str:
        """根据扩展名获取MIME类型"""
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_map.get(ext.lower(), 'image/jpeg')

    def _delete_old_avatar(self, user_id: int):
        """删除用户的旧头像"""
        try:
            self.mongo.delete_many(
                self.collection_name,
                {"user_id": user_id, "file_type": "avatar"}
            )
        except Exception as e:
            print(f"删除旧头像失败: {e}")

    def get_avatar_data_url(self, file_key: Optional[str]) -> str:
        """获取头像的Data URL"""
        try:
            print(f"获取头像Data URL，文件键: {file_key}")

            if not file_key:
                print("文件键为空，使用默认头像")
                file_key = "default_avatar"

            # 从MongoDB获取文件数据
            file_doc = self.mongo.find_one(
                self.collection_name,
                {"file_key": file_key}
            )

            print(f"MongoDB查询结果: {file_doc is not None}")

            if not file_doc:
                print(f"未找到文件: {file_key}")
                # 如果找不到，返回默认头像
                if file_key != "default_avatar":
                    return self.get_avatar_data_url("default_avatar")
                else:
                    # 如果连默认头像都找不到，返回简单的SVG
                    return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjMwIiBmaWxsPSIjY2NjY2NjIi8+PC9zdmc+"

            # 构建Data URL
            mime_type = file_doc.get('mime_type', 'image/jpeg')
            file_data = file_doc.get('file_data', '')

            data_url = f"data:{mime_type};base64,{file_data}"
            print(f"生成Data URL成功，长度: {len(data_url)}")

            return data_url

        except Exception as e:
            print(f"获取头像数据失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回一个简单的默认头像Data URL
            return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjxjaXJjbGUgY3g9IjUwIiBjeT0iNTAiIHI9IjMwIiBmaWxsPSIjY2NjY2NjIi8+PC9zdmc+"

    def delete_avatar(self, file_key: str) -> bool:
        """删除头像"""
        try:
            if file_key == "default_avatar":
                return True  # 不删除默认头像

            result = self.mongo.delete_one(
                self.collection_name,
                {"file_key": file_key}
            )
            return bool(result)
        except Exception as e:
            print(f"删除头像失败: {e}")
            return False

    def get_file_info(self, file_key: str) -> Optional[dict]:
        """获取文件信息"""
        try:
            return self.mongo.find_one(
                self.collection_name,
                {"file_key": file_key},
                {"file_data": 0}  # 不返回文件数据，只返回元信息
            )
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return None

    def get_avatars_batch(self, avatar_keys):
        """批量获取头像Data URL"""
        try:
            if not avatar_keys:
                return {}

            # 去重并过滤空值
            unique_keys = list(set(filter(None, avatar_keys)))

            if not unique_keys:
                return {}

            # 批量查询
            file_docs = self.mongo.find_many(
                self.collection_name,
                {"file_key": {"$in": unique_keys}},
                {"file_key": 1, "mime_type": 1, "file_data": 1}
            )

            # 构建结果字典
            result = {}
            for doc in file_docs:
                file_key = doc.get("file_key")
                mime_type = doc.get("mime_type", "image/jpeg")
                file_data = doc.get("file_data", "")

                if file_key and file_data:
                    result[file_key] = f"data:{mime_type};base64,{file_data}"

            # 为没有找到的头像提供默认值
            default_avatar = self.get_avatar_data_url("default_avatar")
            for key in unique_keys:
                if key not in result:
                    result[key] = default_avatar

            return result

        except Exception as e:
            print(f"批量获取头像失败: {e}")
            return {}

    def get_avatar_data_url_optimized(self, file_key: Optional[str]) -> str:
        """优化的头像获取方法，带缓存"""
        try:
            # 简单的内存缓存
            if not hasattr(self, '_avatar_cache'):
                self._avatar_cache = {}

            cache_key = file_key or "default_avatar"

            # 检查缓存
            if cache_key in self._avatar_cache:
                return self._avatar_cache[cache_key]

            # 获取头像
            data_url = self.get_avatar_data_url(file_key)

            # 缓存结果（限制缓存大小）
            if len(self._avatar_cache) < 100:
                self._avatar_cache[cache_key] = data_url

            return data_url

        except Exception as e:
            print(f"获取头像失败: {e}")
            return self.get_avatar_data_url(None)


# 全局服务实例
mongo_file_service = MongoFileService()
