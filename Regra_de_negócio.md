# 
Conceitos: 
1.	Código de Agendamento: Número gerado pela equipe da logística no SAP para designar um container a ser recebido. A este código estão contidas as notas fiscais dos materiais que estão dentro do container
2.	Cobertura: Período que a quantidade de material supre a demanda: Ex. Se vendo 5 peças por dia, e quero ter 30 dias de cobertura, preciso de 150 peças.
3.	S2GO – Armazém externo. A atividade da S2GO é retirar os materiais de dentro dos containeres, palletizá-los e armazená-los. A equipe no CD realiza pedidos solicitando o retorno, onde os pallets armazenados são separados completos (a quantidade total do pallet é enviada, não há separação unitária) e carregam nas carretas que trarão os materiais de volta para o CD.
4.	Ruptura: Falta de estoque do material (não há saldo)

O Negócio:
	A equipe comercial define a cobertura necessária para cada um dos materiais vendidos. Hoje, a cobertura média para materiais transportados via fluvial (containeres) é de 80 dias.
	Hoje, o Centro de Distribuição não tem espaço suficiente para armazenar a quantidade de material necessário para atingir essa cobertura, principalmente quando se trata de materiais de linha branca (geladeiras, fogões, freezeres...). Por isso, fazemos uso da S2GO.
	O sistema atualmente não permite que as lojas vejam o saldo de material dentro da S2GO para venda a clientes, nem que o DRP veja o saldo para abastecimento de loja.  É necessário que todos os materiais que têm estoque na S2GO, também estejam no CD, para que haja essa visibilidade. 
	A atividade de receber no CD e enviar o excedente para a S2GO é onerosa, pois é necessário deslocar recurso que estaria sendo utilizado para recebimento, para realizar este envio. Por outro lado, por vir palletizada, a carga vinda da S2GO para o CD é facilmente recebida (20min).
	Desta forma, para balancear esta operação, é necessário que os materiais com menor saldo sejam direcionados para o CD, e os outros para a S2GO, considerando as questões de visibilidade e custo de envio.
	Não é possível descarregar parcialmente um container (operação extremamente onerosa, inviável, praticamente impossível).
  
A Avaliação
	A diferença em relação à quantidade de peças que supre a cobertura ideal impacta negativamente, tanto diferença para mais quanto para menos. Mas é preferível receber na S2GO que enviar. Por isso foi determinado pela equipe um parâmetro: 4 carretas de retorno equivalem a 1 carreta de envio. Este será o número utilizado para balancear o cálculo.
	A cobertura utilizada como parâmetro para estoque dentro do CD será de 25 dias, determinada também pela operação, baseado na capacidade de retorno de cargas.
	Vamos somar a quantidade de peças de cada material dentro de um container a quantidade de peças que já temos no CD, e comparar com a ruptura. A menor diferença absoluta será o resultado correto. 
	 
	
