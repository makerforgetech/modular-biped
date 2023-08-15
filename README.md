<h1>SentryBOT Genel Bakış ve Kareler </h1> &nbsp; <h1><a href="https://github.com/SentryCoderDev/SentryBOT/tree/feature/v3serial/SentryBOT fotoğraflar">Fotoğraflar</a></h1>

![V3](https://github.com/SentryCoderDev/SentryBOT/assets/134494889/ff2a8546-a461-4b45-98e1-eed6752441b2)
# Robotik geliştirme çerçevesi
Bu platform, Raspberry Pi/Jetson nano ve Arduino kullanarak Python / C++ ile robotik geliştirme ve deney yapmayı modüler hale getirmek için oluşturulmuştur.

## Coral Usb Hızlandırıcısı

Googla Coral USB Hızlandırıcısını kullanmak için öncelikle Pi SD kartını AIY Maker Kit içinde bulunan görüntüyle yeniden yazdırın.

(Coral başlangıç kılavuzunda yer alan gerekli yazılımı yüklemeye çalıştım, ancak "GLIBC_2.29" bulunamadığına dair bir hata nedeniyle başarılı olamadım.)

Alternatif olarak, Config.VISION_TECH'i opencv olarak ayarlayarak orijinal (daha yavaş) yüz tanıma işlemi için seçim yapabilirsiniz. Bu bölümü artık güncellemiyorum, bu nedenle bazı entegrasyon sorunlarıyla karşılaşabilirsiniz.

## Kurulum
```
chmod 777 install.sh
./install.sh
```

Raspberry pi de neopixelleri kullanmak için sesi devredışı bırakmanız gerekiyor.(neopixel kısmına bakın)

## Çalıştırma
```
./startup.sh
```

Klavye ile manüel kontrol için
```
./manual_startup.sh
```

Başlangıcı gerçekleştirmek için video beslemesinin önizlemesini içeren (SSH aracılığıyla kullanılamaz) 
```
./preview_startup.sh
```

### Test etme
```
python3 -m pytest --cov=modules --cov-report term-missing
```

## Başlangıçta otomatik olarak çalıştırma

`sudo vim /etc/rc/local` komutunu çalıştırın ve `exit 0` ifadesinden önce aşağıdaki satırları ekleyin:
```
python3 /home/Desktop/companion-robot/shutdown_pi.py
/home/Desktop/companion-robot/startup.sh
```

### Düşme anında Otomatik Kapanma
GPIO 26, bir anahtar aracılığıyla toprağa getirildiğinde kapanmayı sağlamak için bağlanmıştır.

shutdown_pi.py betiği bunu yönetmektedir.

Kılavuz:
https://howchoo.com/g/mwnlytk3zmm/how-to-add-a-power-button-to-your-raspberry-pi

## Özellikler

### Yüz tespiti ve Takibi
Raspberry pi kamerası veya herhangi bir webcam kullanılarak

### Servo kontrol
Arduino serial bağlantı ile 8 servo kontrolü(6 servo ayaklar 1 servo pan 1 servo tilt)

### Batarya Monitörü
Harici ve yazılım aracılığıyla Arduino seri bağlantısı üzerinden entegre edilmiştir.

### Buzzer
Bir buzzer, ses çıkışı olmadığında tonların çalınabilmesi için GPIO 27'ye bağlanmıştır (Neopixel kısmına bakın).

https://github.com/gumslone/raspi_buzzer_player.git

### Hareket Sensörü
GPIO 13 üzerine bir RCWL-0516 mikrodalga radar sensörü takılmıştır.

### Stereo MEMS Microfonlar
GPIO 18, 19 ve 20, stereo MEMS mikrofonlarını ses girişi olarak kullanmak için kullanılır.
```
Mic 3V - Pi 3.3V'ye bağlanır.
Mic GND - Pi GND'ye bağlanır.
Mic SEL - Pi GND'ye bağlanır (bu kanal seçimi için kullanılır, 3.3V veya GND'ye bağlanabilir).
Mic BCLK - BCM 18 (pin 12)'e bağlanır.
Mic DOUT - BCM 20 (pin 38)'ye bağlanır.
Mic LRCL - BCM 19 (pin 35)'e bağlanır.
```
https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test


```
cd ~
sudo pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2smic.py
sudo python3 i2smic.py
```

#### Test etme
`arecord -l`
`arecord -D plughw:0 -c2 -r 48000 -f S32_LE -t wav -V stereo -v file_stereo.wav`

_Note:_ Ses tanıma işlemini desteklemek için aşağıdaki ek yapılandırmaya bakın.

### Hotword
Orijinal sıcak kelime algılama, artık kullanımdan kaldırılan Snowboy'u kullanmaktaydı. Dosyalar hala bu depoda mevcuttur:

https://github.com/dmt-labs/modular-biped/blob/feature/PR29_review/modules/hotword.py, bu çerçeveden gelen modülü içerir.

https://github.com/dmt-labs/modular-biped/tree/feature/PR29_review/modules/snowboy, orijinal snowboy işlevselliğini içerir.

https://github.com/dmt-labs/modular-biped/tree/feature/PR29_review/modules/snowboy/resources/models, anahtar kelimeler olarak kullanılabilecek eğitilmiş modelleri içerir. İnternet üzerinde daha fazlasını bulmak mümkün olabilir.

Yeni modellerin eğitimi konusunda bir rehber burada bulunmaktadır ama linux bir cihazda yeni modeller eğitmek için kaynaklar bulunmaktadır.

### Konuşma Tanıma
Ses tanıma için tetikleyici kelime (şu anda kullanılmıyor):
https://snowboy.kitt.ai/

Yüz görüldüğünde konuşma tanıma etkinleştirilir.
`modules/speechinput.py` dosyasında belirtilen `device_index` değerinin mikrofonunuzla eşleştiğinden emin olun.

Giriş cihazlarını listelemek ve test etmek için `scripts/speech.py` dosyasına bakın. MEMS mikrofon yapılandırması için aşağıya bakın.
### Konuşma Tanıma için MEMS Mikrofon konfigrasyonu

Varsayılan olarak, Adafruit I2S MEMS Mikrofon Breakout, ses tanıma ile çalışmaz.

MEMS mikrofon(lar) üzerinde ses tanımayı desteklemek için aşağıdaki yapılandırma değişiklikleri yapılmalıdır.

`sudo apt-get install ladspa-sdk`
Aşağıdaki içeriğe `/etc/asound.conf`dosyası oluşturun:

``` 
pcm.pluglp {
    type ladspa
    slave.pcm "plughw:0"
    path "/usr/lib/ladspa"
    capture_plugins [
   {   
      label hpf
      id 1042
   }
        {
                label amp_mono
                id 1048
                input {
                    controls [ 30 ]
                }
        }
    ]
}

pcm.lp {
    type plug
    slave.pcm pluglp
}
```

Bu, ses tanımada 'lp' cihazının başvurulabilmesini sağlar. Aşağıdaki örnekte `18` dizininde gösterilir.

Örneğin, örnekleme hızı `16000` olarak ayarlanmalıdır.

`mic = sr.Microphone(device_index=18, sample_rate=16000)`

Referanslar:

* [MEMS Microphone Installation Guide](https://learn.adafruit.com/adafruit-i2s-mems-microphone-breakout/raspberry-pi-wiring-test)

* [Adafruit Support discussing issue](https://forums.adafruit.com/viewtopic.php?f=50&t=181675&p=883853&hilit=MEMS#p883853)

* [Referenced documentation of fix](https://github.com/mpromonet/v4l2rtspserver/issues/94)

### Arduino ile seri haberleşme

Raspberry Pi'nin seri portunu kullanabilmek için, getty (giriş ekranını görüntüleyen program) devre dışı bırakılmalıdır.

`sudo raspi-config ->  Interfacing Options -> Serial -> "Would you like a login shell to be accessible over serial" = 'No'. Restart`

#### Serial pinleri ile bağlantı
Raspberry Pi'nin GPIO 14 ve 15 (tx ve rx) pinlerini, Arduino tx ve rx pinlerine (hem yönü hem de yönü tersine olarak tx -> rx!) bir mantıksal seviye kaydırıcı aracılığıyla bağlayın, çünkü Raspberry Pi 3v3 ve Arduino (muhtemelen) 5v'dur.

#### Arduino'ya seri pinler aracılığıyla yükleme yapmak için aşağıdaki adımı izleyebilirsiniz:

Seri pinler aracılığıyla yükleme yapmak için, IDE 'uploading' (derlemeden sonra) işlemine başladığı noktada Arduino üzerindeki reset düğmesine basın; aksi takdirde senkronizasyon hatası görüntülenecektir.

### Neopixel

Pi GPIO pin 12 üzerinden WS1820B desteği sağlanmıştır. Ne yazık ki, bunu desteklemek için Pi üzerindeki ses devre dışı bırakılmalıdır.

```
sudo vim /boot/config.txt
#dtparam=audio=on
```

Bu nedenle uygulamanın `sudo` ile çalıştırılması gerekmektedir.

Eğer sürücüyü kullanmadan neopixelleri kullanmak isterseniz (ve ses çıkışı olmadan), yapılandırmada pini 12 olarak ayarlayın ve i2c'yi False olarak ayarlayın. Uygulama ayrıca sudo ile çalıştırılmalıdır.

https://learn.adafruit.com/neopixels-on-raspberry-pi/python-usage

### Anlık Çeviri

Canlı çeviri modülü <code>translation.py</code> günlüklerin ve TTS çıkısının Google Çeviri aracılığıyla canlı çevirisine olanak tanır.

<code>translate.request(msg)</code> işlevini çağırın ve isteğe bağlı olarak kaynak ve hedef dilleri belirtin.

<code>config/translation.yml</code> varsayılan dilleri belirtir.


## PCBler
Bu projenin prefabrike PCB'leri `circuits` klasöründe mevcuttur. Bu, yukarıda açıklandığı şekilde çekirdek bileşenler arasında bağlantı sağlar.

![Top](Devreler/v2/Upper/Top%20Feb%202021_pcb.png)

![body_pcb](https://github.com/SentryCoderDev/SentryBOT/assets/134494889/857f3284-5361-4b6f-b097-b052fe510902)

