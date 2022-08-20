curl -X "POST" ^
  "http://localhost:8100/match_products" ^
  -H "accept: application/json" ^
  -H "Content-Type: application/json" ^
  -d @test.json -o test.output.json
