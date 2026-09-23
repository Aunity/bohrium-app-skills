# <App Name> Bohrium App 基础信息草案

> 状态：基础信息草案  
> 创建日期：<YYYY-MM-DD>  
> 参考页面：<optional Bohrium reference URL>  
> 本文只覆盖 App 上架基础资料；镜像、运行参数、资源规格、License、发布检查后续补齐。

## 1. 控台基础字段

| 字段 | 建议填写 |
| --- | --- |
| App 标识 / appKey | `<app-key>` |
| App 名称 / App name | `<App Name>` |
| 中文描述 | <one-sentence Chinese listing description> |
| 英文描述 | <one-sentence English listing description> |
| 中文帮助文档名 | `<Chinese Help Title>` |
| 英文帮助文档名 | `<English Help Title>` |
| 封面图片 | `<assets/cover/app-key-cover.png or pending>` |
| 建议 App 类型 | <标准离线任务 / Custom Web / MCP / 待确认> |
| 建议标签 | `<tag-1>`, `<tag-2>`, `<tag-3>` |

封面预览：

![<App Name> cover](../assets/cover/<app-key>-cover.png)

## 2. App 介绍（中文）

<Chinese introduction with numbered references where needed, e.g. [1][2].>

<Second paragraph covering expected user workflow and outputs. Mark future or unimplemented behavior clearly.>

<Scientific/product disclaimer.>

### 参考文献

[1] <Chinese-page source citation and URL>

## 3. App Introduction (English)

<English introduction with numbered references where needed, e.g. [1][2].>

<Second paragraph covering expected user workflow and outputs. Mark future or unimplemented behavior clearly.>

<Scientific/product disclaimer.>

### References

[1] <English-page source citation and URL>

## 4. 帮助文档草案（中文）

### <Chinese Help Title>

#### 输入

- <input item>

#### 输出

- `<output file>`：<meaning>

#### 结果解读

<How users should interpret outputs.>

#### 注意事项

- <limitation or failure mode>

#### 参考文献

[1] <Chinese-help source citation and URL, or write "无外部参考">

## 5. Help Draft (English)

### <English Help Title>

#### Inputs

- <input item>

#### Outputs

- `<output file>`: <meaning>

#### Interpreting Results

<How users should interpret outputs.>

#### Notes

- <limitation or failure mode>

#### References

[1] <English-help source citation and URL, or write "No external references">

## 6. 后续镜像与运行契约待补

| 模块 | 待确认内容 |
| --- | --- |
| 科学入口 | <upstream tool/model/fork/entrypoint> |
| 输入格式 | <files, IDs, chain selection, batch limits> |
| 表单参数 | <user-facing parameters and validation rules> |
| 运行资源 | <CPU/GPU, memory, disk, expected duration> |
| 镜像依赖 | <language, packages, system binaries, model weights> |
| 结果契约 | `result.json` schema、CSV 列名、可视化文件格式、失败状态定义。 |
| License | <source/model/binary/data license checks> |
| 发布证据 | <local smoke, clean image job, Preview, App page checks> |

## 7. Internal Evidence / 内部证据记录

<Optional planning evidence. Do not rely on this section as the only citation location for the four independent Markdown-rendered pages.>

## 8. 封面图生成记录

生成方式：<image_gen / existing asset / pending>。  
最终文件：`assets/cover/<app-key>-cover.png`。

生成提示摘要：

```text
<cover prompt summary>
```
