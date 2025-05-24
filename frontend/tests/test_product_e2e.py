import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ProductE2ETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 请根据实际chromedriver路径修改
        service = Service('D:/workplace/chromedriver-win64/chromedriver.exe')
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.maximize_window()
        cls.base_url = 'http://localhost:5174'  # 前端服务地址

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def login(self):
        driver = self.driver
        driver.get(f'{self.base_url}/login')
        # 请根据实际页面元素修改
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="请输入邮箱"]')))
        driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入邮箱"]').send_keys('admin@example.com')
        driver.find_element(By.CSS_SELECTOR, 'input[placeholder="请输入密码"]').send_keys('admin123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        # 等待跳转到首页
        WebDriverWait(driver, 10).until(EC.url_contains('/'))

    def test_product_crud(self):
        driver = self.driver
        self.login()
        # 进入商品管理页
        driver.get(f'{self.base_url}/product')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button//span[text()="新增商品"]')))
        driver.find_element(By.XPATH, '//button//span[text()="新增商品"]').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="name"]')))
        driver.find_element(By.XPATH, '//input[@id="name"]').send_keys('自动化商品')
        driver.find_element(By.XPATH, '//input[@id="sku"]').send_keys('AUTO001')
        driver.find_element(By.XPATH, '//input[@id="unit"]').send_keys('件')
        driver.find_element(By.XPATH, '//input[@id="status"]').clear()
        driver.find_element(By.XPATH, '//input[@id="status"]').send_keys('1')
        driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
        # 检查新增成功
        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, '//td'), '自动化商品'))
        # 编辑商品
        driver.find_element(By.XPATH, '//span[text()="编辑"]').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//input[@id="name"]')))
        name_input = driver.find_element(By.XPATH, '//input[@id="name"]')
        name_input.clear()
        name_input.send_keys('自动化商品-改')
        driver.find_element(By.XPATH, '//button/span[text()="确定"]').click()
        WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, '//td'), '自动化商品-改'))
        # 删除商品
        driver.find_element(By.XPATH, '//span[text()="删除"]').click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//button/span[text()="删除"]')))
        driver.find_element(By.XPATH, '//button/span[text()="删除"]').click()  # 确认删除
        time.sleep(1)
        # 检查删除成功
        self.assertNotIn('自动化商品-改', driver.page_source)

if __name__ == '__main__':
    unittest.main() 