import time
import random
import string
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chromedriver_path = "D:/workplace/chromedriver-win64/chromedriver.exe"
frontend_url = "http://localhost:5173"
backend_url = "http://192.168.31.71:5000"

# 结果收集
TEST_RESULT_FILE = "test_result.txt"
results = []

def log_result(case, success, msg=""):
    results.append(f"{case}: {'PASS' if success else 'FAIL'} {msg}")
    with open(TEST_RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(f"{case}: {'PASS' if success else 'FAIL'} {msg}\n")

def random_email():
    return f"test_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}@example.com"

def random_phone():
    return "13" + ''.join(random.choices(string.digits, k=9))

def random_username():
    return "admin" + ''.join(random.choices(string.digits, k=3))

class FullE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        service = Service(executable_path=chromedriver_path)
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.maximize_window()
        cls.email = random_email()
        cls.password = "Test123456"
        cls.merchant_name = "测试商家"
        cls.phone = random_phone()
        cls.username = random_username()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_register(self):
        driver = self.driver
        driver.get(f"{frontend_url}/register")
        time.sleep(1)
        try:
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入商家名称']").send_keys(self.merchant_name)
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入邮箱']").send_keys(self.email)
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入手机号']").send_keys(self.phone)
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入管理员用户名']").send_keys(self.username)
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']").send_keys(self.password)
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请再次输入密码']").send_keys(self.password)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)
            self.assertTrue("注册成功" in driver.page_source or "登录" in driver.page_source)
            log_result("注册", True)
        except Exception as e:
            log_result("注册", False, str(e))
            raise

    def test_02_login(self):
        driver = self.driver
        driver.get(f"{frontend_url}/login")
        time.sleep(1)
        try:
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入邮箱']").send_keys(self.email)
            driver.find_element(By.CSS_SELECTOR, "input[placeholder='请输入密码']").send_keys(self.password)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(2)
            self.assertTrue("欢迎" in driver.page_source or "仪表盘" in driver.page_source)
            log_result("登录", True)
        except Exception as e:
            log_result("登录", False, str(e))
            raise

    def test_03_dashboard(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/dashboard")
            time.sleep(1)
            self.assertIn("仪表盘", driver.page_source)
            log_result("仪表盘页面", True)
        except Exception as e:
            log_result("仪表盘页面", False, str(e))
            raise

    def test_04_product_crud(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/product")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button//span[text()="新增商品"]')))
            driver.find_element(By.XPATH, '//button//span[text()="新增商品"]').click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="name"]')))
            driver.find_element(By.XPATH, '//input[@id="name"]').send_keys('自动化商品')
            driver.find_element(By.XPATH, '//input[@id="sku"]').send_keys('AUTO001')
            driver.find_element(By.XPATH, '//input[@id="unit"]').send_keys('件')
            driver.find_element(By.XPATH, '//input[@id="status"]').clear()
            driver.find_element(By.XPATH, '//input[@id="status"]').send_keys('1')
            driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
            WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, '//td'), '自动化商品'))
            log_result("商品新增", True)
            # 编辑
            driver.find_element(By.XPATH, '//span[text()="编辑"]').click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="name"]')))
            name_input = driver.find_element(By.XPATH, '//input[@id="name"]')
            name_input.clear()
            name_input.send_keys('自动化商品-改')
            driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
            WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, '//td'), '自动化商品-改'))
            log_result("商品编辑", True)
            # 删除
            driver.find_element(By.XPATH, '//span[text()="删除"]').click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//button/span[text()="删除"]')))
            driver.find_element(By.XPATH, '//button/span[text()="删除"]').click()
            time.sleep(1)
            self.assertNotIn('自动化商品-改', driver.page_source)
            log_result("商品删除", True)
        except Exception as e:
            log_result("商品CRUD", False, str(e))
            raise

    def test_05_inventory(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/inventory")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//span[text()="盘点"]')))
            driver.find_element(By.XPATH, '//span[text()="盘点"]').click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="quantity"]')))
            quantity_input = driver.find_element(By.XPATH, '//input[@id="quantity"]')
            quantity_input.clear()
            quantity_input.send_keys('100')
            driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
            time.sleep(1)
            driver.find_element(By.XPATH, '//span[text()="告警设置"]').click()
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="warning_line"]')))
            warning_input = driver.find_element(By.XPATH, '//input[@id="warning_line"]')
            warning_input.clear()
            warning_input.send_keys('10')
            driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
            time.sleep(1)
            self.assertIn('库存', driver.page_source)
            log_result("库存盘点与告警", True)
        except Exception as e:
            log_result("库存盘点与告警", False, str(e))
            raise

    def test_06_order(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/order")
            time.sleep(1)
            self.assertIn('订单', driver.page_source)
            log_result("订单页面", True)
        except Exception as e:
            log_result("订单页面", False, str(e))
            raise

    def test_07_permission(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/permission")
            time.sleep(1)
            self.assertIn('权限', driver.page_source)
            log_result("权限页面", True)
        except Exception as e:
            log_result("权限页面", False, str(e))
            raise

    def test_08_alert(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/alert")
            time.sleep(1)
            self.assertIn('告警', driver.page_source)
            log_result("告警页面", True)
        except Exception as e:
            log_result("告警页面", False, str(e))
            raise

    def test_09_log(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/log")
            time.sleep(1)
            self.assertIn('日志', driver.page_source)
            log_result("日志页面", True)
        except Exception as e:
            log_result("日志页面", False, str(e))
            raise

    def test_10_message(self):
        driver = self.driver
        try:
            driver.get(f"{frontend_url}/message")
            time.sleep(1)
            self.assertIn('消息', driver.page_source)
            log_result("消息页面", True)
        except Exception as e:
            log_result("消息页面", False, str(e))
            raise

if __name__ == "__main__":
    # 清空历史测试结果
    with open(TEST_RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("")
    unittest.main() 