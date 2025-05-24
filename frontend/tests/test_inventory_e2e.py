import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class InventoryE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        service = Service('D:/workplace/chromedriver-win64/chromedriver.exe')
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.maximize_window()
        cls.base_url = 'http://localhost:5174'

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def login(self):
        driver = self.driver
        driver.get(f'{self.base_url}/login')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="请输入邮箱"]')))
        driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入邮箱"]').send_keys('admin@example.com')
        driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入密码"]').send_keys('admin123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        WebDriverWait(driver, 10).until(EC.url_contains('/'))

    def test_inventory_check_and_warning(self):
        driver = self.driver
        self.login()
        driver.get(f'{self.base_url}/inventory')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//span[text()="盘点"]')))
        # 盘点操作
        driver.find_element(By.XPATH, '//span[text()="盘点"]').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="quantity"]')))
        quantity_input = driver.find_element(By.XPATH, '//input[@id="quantity"]')
        quantity_input.clear()
        quantity_input.send_keys('100')
        driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
        time.sleep(1)
        # 告警设置
        driver.find_element(By.XPATH, '//span[text()="告警设置"]').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="warning_line"]')))
        warning_input = driver.find_element(By.XPATH, '//input[@id="warning_line"]')
        warning_input.clear()
        warning_input.send_keys('10')
        driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
        time.sleep(1)
        # 检查页面反馈
        self.assertIn('库存', driver.page_source)

if __name__ == '__main__':
    unittest.main() 