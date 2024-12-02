import os

def delete_files_in_subdirectories(root_dir, prefixes):
    """
    删除指定目录下所有以特定前缀开头的文件。

    :param root_dir: 根目录路径
    :param prefixes: 文件名前缀列表
    """
    # 遍历根目录下的所有子目录
    for subdir in os.listdir(root_dir):
        if subdir.startswith('sub'):
            subdir_path = os.path.join(root_dir, subdir)
            if os.path.isdir(subdir_path):
                # 遍历子目录中的所有文件
                for filename in os.listdir(subdir_path):
                    file_path = os.path.join(subdir_path, filename)
                    if os.path.isfile(file_path):
                        # 检查文件名是否以指定前缀开头
                        if any(filename.startswith(prefix) for prefix in prefixes):
                            print(f"Deleting file: {file_path}")
                            os.remove(file_path)

if __name__ == "__main__":
    # 当前目录
    current_dir = os.getcwd()
    # 要删除的文件前缀
    prefixes_to_delete = ['case', 'dialogue', 'raw']
    
    # 执行删除操作
    delete_files_in_subdirectories(current_dir, prefixes_to_delete)