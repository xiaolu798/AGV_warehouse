import pandas as pd
import io


def main(arg1: list):
    # 1. 检查是否有文件上传
    if not arg1 or len(arg1) == 0:
        return {"result": "未检测到上传文件"}

    try:
        # 2. 获取文件对象（Dify 传入的是文件对象列表）
        file_obj = arg1[0]

        # 3. 读取文件内容
        # 如果是 Excel (.xlsx, .xls)，如果是 CSV 则改用 read_csv
        # 注意：Dify 沙盒环境可能需要通过 file_obj.url 或直接读取二进制流
        if file_obj.extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_obj)
        else:
            df = pd.read_csv(file_obj)

        # 4. 数据预处理：只取前 20 行，防止数据量太大撑爆 LLM 上下文
        df_summary = df.head(20)

        # 5. 转换为 JSON 字符串输出，方便后续 LLM 生成 ECharts 配置
        data_json = df_summary.to_json(orient='records', force_ascii=False)

        return {
            "result": f"已成功读取文件，前20行数据如下：\n{data_json}"
        }

    except Exception as e:
        return {"result": f"解析失败：{str(e)}"}
