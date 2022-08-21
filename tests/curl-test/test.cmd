@echo off
set input_file=%~1
if "%input_file%" == "" (
  set input_file=test.json
)
set output_file=%input_file%.output.json
curl -X "POST" ^
  "http://localhost:8100/match_products" ^
  -H "accept: application/json" ^
  -H "Content-Type: application/json" ^
  -d "@%input_file%" -o %output_file%
