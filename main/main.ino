#include <TimerOne.h>

#define BIAS 16
const int signalPin = A0;
int sample_rate = 1000;
int delay_us;

int minY = 0;
int maxY = 0;

void plot(int value)
{
  if (value > maxY)
    maxY = value;
  Serial.print(minY);
  Serial.print(" ");
  Serial.print(maxY);
  Serial.print(" ");
  Serial.println(value);
}

void interrupt_handler()
{
  //Serial.println(micros());
  //plot(analogRead(signalPin) + BIAS);
  Serial.write(analogRead(signalPin) + BIAS);
}

void setup(void)
{
  sample_rate *= 2;
  delay_us = 1000000 / sample_rate;
  Serial.begin(115200);
  Timer1.initialize(delay_us);
  Timer1.attachInterrupt(interrupt_handler);
}

void loop()
{
}
