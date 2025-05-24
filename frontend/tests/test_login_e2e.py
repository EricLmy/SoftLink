from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
import random
import string

chromedriver_path = "D:/workplace/chromedriver-win64/chromedriver.exe"

def random_email():
    return f"test_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}@example.com"

def test_register_and_login():
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("http://localhost:5173/register")
    driver.maximize_window()
    time.sleep(1)

    # 随机生成注册信息
    email = random_email()
    password = "Test123456"
    merchant_name = "测试商家"
    phone = "13800000000"
    username = "admin" + ''.join(random.choices(string.digits, k=3))

    # 填写注册表单
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入商家名称']").send_keys(merchant_name)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入邮箱']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入手机号']").send_keys(phone)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入管理员用户名']").send_keys(username)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请再次输入密码']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    # 检查注册成功提示
    assert "注册成功" in driver.page_source or "登录" in driver.page_source

    # 跳转到登录页，执行登录
    driver.get("http://localhost:5173/login")
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入邮箱']").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)
    assert "欢迎" in driver.page_source or "仪表盘" in driver.page_source

    driver.quit()

def test_login_page():
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("http://localhost:5173/login")
    driver.maximize_window()
    time.sleep(1)

    # 检查页面元素
    assert "登录" in driver.page_source
    assert "邮箱" in driver.page_source
    assert "密码" in driver.page_source

    # 输入邮箱、密码
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入邮箱']").send_keys("test@example.com")
    driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']").send_keys("12345678")

    # 点击登录按钮
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    # 检查是否跳转到主页面或有"欢迎"字样
    assert "欢迎" in driver.page_source or "仪表盘" in driver.page_source

    driver.quit()

if __name__ == "__main__":
    test_register_and_login()
    test_login_page() 