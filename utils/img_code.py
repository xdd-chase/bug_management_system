import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def check_code(width=120, height=30, char_length=5, font_file='utils/kumo.ttf', font_size=32):
    """

    :param width: 画布宽度
    :param height: 画布高度
    :param char_length: 图片验证码重点字母个数
    :param font_file: 字体文件
    :param font_size: 字体大小
    :return: 图片和验证码
    """
    code = []
    # 创建画布
    img = Image.new(mode='RGB', size=(width, height), color=(255, 255, 255))
    # 创建画笔
    draw = ImageDraw.Draw(img, mode='RGB')

    def rand_char():
        """
        生成随机字母
        :return:
        """
        return chr(random.randint(65, 90))

    def rand_color():
        """
        生成随机颜色
        :return:
        """
        return random.randint(0, 150), random.randint(10, 100), random.randint(64, 255)

    # 写文字
    # 第一个参数：表示字体文件路径,第二个参数：表示字体大小
    font = ImageFont.truetype(font_file, font_size)
    for i in range(char_length):
        char = rand_char()
        code.append(char)
        h = random.randint(0, 4)
        # 第一个参数：表示起始坐标,第二个参数：表示写入内容,第三个参数：表示字体,第四个参数：表示颜色
        draw.text([i * width / char_length, h], char, font=font, fill=rand_color())

    # 写干扰点
    for i in range(30):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rand_color())

    # 写干扰圆圈
    for i in range(20):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=rand_color())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=rand_color())

    # 画干扰线
    for i in range(2):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)

        draw.line((x1, y1, x2, y2), fill=rand_color())
    # 在尽量保留图像细节特征的条件下对目标图像的噪声进行抑制
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img, ''.join(code)


if __name__ == '__main__':
    img_object, code = check_code()
    print(code)
    with open('../scripts/code.png', 'wb') as f:
        img_object.save(f, format='png')

# 3. 写入内存(Python3)
# from io import BytesIO
# stream = BytesIO()
# img.save(stream, 'png')
# stream.getvalue()

# 4. 写入内存（Python2）
# import StringIO
# stream = StringIO.StringIO()
# img.save(stream, 'png')
# stream.getvalue()
