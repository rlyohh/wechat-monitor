import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import ssl
import os
import json


def send_email(subject, body, to_email, smtp_config):
    """发送邮件 - GitHub Actions版本"""
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        print(f"🔄 连接SMTP服务器: {smtp_config['smtp_server']}:{smtp_config['smtp_port']}")
        
        try:
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            server.starttls()
            server.login(smtp_config['from_email'], smtp_config['password'])
            
            text = msg.as_string()
            server.sendmail(smtp_config['from_email'], to_email, text)
            server.quit()
            
            print(f"✅ 邮件已发送到: {to_email}")
            return True
            
        except Exception as e:
            print(f"⚠️  STARTTLS失败: {e}")
            
            try:
                print("🔄 尝试SSL连接...")
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_config['smtp_server'], 465, context=context) as server:
                    server.login(smtp_config['from_email'], smtp_config['password'])
                    text = msg.as_string()
                    server.sendmail(smtp_config['from_email'], to_email, text)
                    
                print(f"✅ 邮件已发送 (SSL): {to_email}")
                return True
                
            except Exception as e2:
                print(f"❌ 邮件发送失败: {e2}")
                return False

    except Exception as e:
        print(f"❌ 邮件发送错误: {e}")
        return False


def get_absolute_url(base_url, href):
    """将相对URL转换为绝对URL"""
    from urllib.parse import urljoin
    return urljoin(base_url, href)


def load_last_status():
    """加载上次的状态记录"""
    try:
        status_file = os.path.join(os.path.dirname(__file__), 'last_status.json')
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️  加载状态文件失败: {e}")
    return {}


def save_current_status(status_data):
    """保存当前状态"""
    try:
        status_file = os.path.join(os.path.dirname(__file__), 'last_status.json')
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        print("💾 状态已保存")
    except Exception as e:
        print(f"⚠️  保存状态失败: {e}")


def monitor_RoomsX_status(url, email_config):
    """监控RoomsX状态"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        h3_tags = soup.find_all('h3')

        current_items = []
        open_items = []

        for h3 in h3_tags:
            if h3.get_text(strip=True) == 'RoomsX':
                next_sibling = h3.find_next_sibling('p')

                if next_sibling:
                    content = next_sibling.get_text(strip=True)
                    
                    # 获取链接
                    parent_a = h3.find_parent('a')
                    absolute_url = "未找到链接"

                    if parent_a and parent_a.get('href'):
                        href_link = parent_a.get('href')
                        absolute_url = get_absolute_url(url, href_link)

                    item_info = {
                        'h3_content': h3.get_text(strip=True),
                        'p_content': content,
                        'status': content,
                        'link': absolute_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    current_items.append(item_info)

                    if content.upper() == 'OPEN':
                        open_items.append(item_info)

        # 检查状态变化
        last_status = load_last_status()
        newly_opened = []

        for item in open_items:
            item_key = f"{item['h3_content']}_{item['link']}"
            if item_key not in last_status.get('open_items', {}):
                newly_opened.append(item)

        # 保存当前状态
        current_status = {
            'open_items': {f"{item['h3_content']}_{item['link']}": item for item in open_items},
            'all_items': current_items,
            'last_check': datetime.now().isoformat()
        }
        save_current_status(current_status)

        # 输出结果
        print(f"🔍 检查完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 找到 {len(current_items)} 个RoomsX项目")
        print(f"🟢 当前OPEN状态: {len(open_items)} 个")
        print(f"🆕 新增OPEN状态: {len(newly_opened)} 个")

        for item in current_items:
            status_emoji = "🟢" if item['status'].upper() == 'OPEN' else "🔴"
            print(f"  {status_emoji} {item['h3_content']}: {item['p_content']} | {item['link']}")

        # 只对新增的OPEN状态发送邮件
        if newly_opened:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = f"🚨 RoomsX状态变更通知 - {len(newly_opened)}个新OPEN状态"

            links_info = []
            for i, item in enumerate(newly_opened, 1):
                links_info.append(f"{i}. 项目: {item['h3_content']}")
                links_info.append(f"   状态: {item['p_content']}")
                links_info.append(f"   链接: {item['link']}")
                links_info.append("")

            body = f"""
🎉 检测到RoomsX状态新变更为OPEN！

⏰ 检测时间: {current_time}
🌐 监控网址: {url}
📊 新OPEN状态数量: {len(newly_opened)}
📈 当前总OPEN数量: {len(open_items)}

📋 新OPEN项目详情:
{chr(10).join(links_info)}

💡 提示: 请尽快访问链接查看详情！

🤖 GitHub Actions自动监控系统
            """

            if send_email(subject, body, email_config['to_email'], email_config['smtp']):
                print("✅ 新OPEN状态邮件通知已发送")
            else:
                print("❌ 邮件发送失败")
        else:
            print("ℹ️  没有新的OPEN状态")

        return len(newly_opened) > 0

    except Exception as e:
        print(f"❌ 监控错误: {e}")
        return False


def main():
    """主函数"""
    print("🚀 GitHub Actions - RoomsX状态监控")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # 从环境变量读取配置
    email_config = {
        'to_email': os.getenv('TO_EMAIL'),
        'smtp': {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.qq.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'from_email': os.getenv('FROM_EMAIL'),
            'password': os.getenv('EMAIL_PASSWORD')
        }
    }
    
    # 验证配置
    if not all([email_config['to_email'], email_config['smtp']['from_email'], email_config['smtp']['password']]):
        print("❌ 缺少必要的环境变量配置!")
        print("请设置: TO_EMAIL, FROM_EMAIL, EMAIL_PASSWORD")
        return False
    
    url = "https://departures.to/tags/chat"
    
    try:
        has_new_open = monitor_RoomsX_status(url, email_config)
        print(f"📊 监控完成: {'发现新状态' if has_new_open else '无新变化'}")
        return True
    except Exception as e:
        print(f"❌ 监控失败: {e}")
        return False


if __name__ == "__main__":
    main()
