from nonebot.adapters.telegram import Message

guide = """
*🔑 获取芝麻粒\-TK授权ID指南*

1\. 在手机文件管理中找到路径：  
`/storage/emulated/0/Android/media/com.eg.android.AlipayGphone/sesame\-TK/config/xxxx/self.json`

2\. 打开 `self.json` 文件找到 `userId` 字段 \(`your_id`\)  
3\. 模块首页长按获取验证ID \(`verify_id`\)

📌 请按照以下格式发送命令进行绑定，中间用空格分隔开

`/sync`  同步账户状态，生成绑定码  
`/bd verify_id`  绑定验证id \(模块版本大于0\.2\.7\.rc2340 不卸载模块此ID不再发生变化\) 
`/ba userId`  绑定支付宝id

绑定错了写作文联系 @Fansirsqi 不少于 `800` 字 💢  
禁止瞎绑定不是自己的号 💢  
如有人绑定错了你的 ID，带上你的 ID 凭证联系我，乱绑定不是你自己的也统一封禁 💢
"""

guide_msg: Message = Message(guide)
